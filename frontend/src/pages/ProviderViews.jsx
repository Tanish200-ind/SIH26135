import { useState } from "react";
import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import { Loading, ErrorState, Section } from "../components/PageKit.jsx";

// Provider workflow: create a new training programme. The backend resolves
// ownership from the JWT — the form never sends a provider id.
function AddProgramForm({ onCreated }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [weeks, setWeeks] = useState("8");
  const [progStatus, setProgStatus] = useState("active");
  const [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const skills = useApi(() => api.skills(accessToken()));

  function toggleSkill(id) {
    setSelected((cur) =>
      cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]
    );
  }

  async function submit(e) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) return setError("Programme name is required.");
    if (!selected.length) return setError("Select at least one skill taught.");
    const weeksNum = Number.parseInt(weeks, 10);
    if (!Number.isFinite(weeksNum) || weeksNum < 1)
      return setError("Duration must be at least 1 week.");
    setBusy(true);
    try {
      await api.createProgram(
        {
          name: name.trim(),
          description: description.trim(),
          duration_weeks: weeksNum,
          status: progStatus,
          skill_ids: selected,
        },
        accessToken()
      );
      setName("");
      setDescription("");
      setWeeks("8");
      setSelected([]);
      setProgStatus("active");
      setOpen(false);
      onCreated && onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Section
      title="Create a programme"
      meta="Skills taught come from the official skill catalog"
    >
      {!open ? (
        <button type="button" className="btn btn-primary" onClick={() => setOpen(true)}>
          + Add Program
        </button>
      ) : (
        <form className="wf-form" onSubmit={submit}>
          <div className="form-grid">
            <label className="field">
              <span>Programme name</span>
              <input
                className="wf-input"
                value={name}
                maxLength={200}
                placeholder="e.g. Drone Pilot Basics"
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <label className="form-split">
              <span className="form-half">
                <span>Duration (weeks)</span>
                <input
                  className="wf-input"
                  type="number"
                  min={1}
                  max={200}
                  value={weeks}
                  onChange={(e) => setWeeks(e.target.value)}
                />
              </span>
              <span className="form-half">
                <span>Status</span>
                <select
                  className="wf-select"
                  value={progStatus}
                  onChange={(e) => setProgStatus(e.target.value)}
                >
                  <option value="active">active</option>
                  <option value="closed">closed</option>
                </select>
              </span>
            </label>
            <label className="form-grid">
              <span>Description (optional)</span>
              <textarea
                className="wf-input"
                rows={2}
                value={description}
                placeholder="Short summary shown to trainees"
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
          </div>

          <div className="skill-picker">
            <span className="picker-label">Skills taught</span>
            {skills.loading && <span className="muted">Loading skills…</span>}
            {skills.error && <span className="wf-error">Could not load skills: {skills.error}</span>}
            <div className="chips">
              {(skills.data || []).map((s) => (
                <button
                  type="button"
                  key={s.id}
                  className={`chip ${selected.includes(s.id) ? "chip-on" : ""}`}
                  onClick={() => toggleSkill(s.id)}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="wf-error">{error}</p>}
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Creating…" : "Create programme"}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => { setOpen(false); setError(null); }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </Section>
  );
}

// Training-provider role view: only read endpoints the provider may access
// (own programmes, the trainee roster, and the employment table).
export default function ProviderOverview() {
  const programs = useApi(() => api.programs(accessToken()));
  const trainees = useApi(() => api.trainees(accessToken()));
  const employment = useApi(() => api.employment(accessToken()));

  const loading = programs.loading || trainees.loading || employment.loading;
  const failed = programs.error || trainees.error || employment.error;

  if (loading) return <Loading label="Loading provider overview…" />;
  if (failed) return <ErrorState message={failed} hint="Provider access is required." />;

  return (
    <div className="stack">
      <AddProgramForm onCreated={() => programs.refresh()} />

      <Section title="Your programmes" meta={`${(programs.data || []).length} programmes`}>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Programme</th>
                <th className="num">Duration (wk)</th>
                <th>Status</th>
                <th>Skills taught</th>
              </tr>
            </thead>
            <tbody>
              {(programs.data || []).map((p) => (
                <tr key={p.id}>
                  <td>
                    <div className="cell-title">{p.name}</div>
                    <div className="cell-sub">{p.provider_name}</div>
                  </td>
                  <td className="num">{p.duration_weeks}</td>
                  <td>
                    <span className={`tag ${p.status === "active" ? "tag-ok" : "tag-warn"}`}>{p.status}</span>
                  </td>
                  <td className="cell-sub">{(p.skills || []).map((s) => s.name).join(" · ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <div className="panel-row two">
        <Section title="Trainee roster" meta={`${(trainees.data || []).length} trainees`}>
          <div className="table-wrap">
            <table className="table compact">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>District</th>
                  <th>Education</th>
                  <th>Skills</th>
                </tr>
              </thead>
              <tbody>
                {(trainees.data || []).map((t) => (
                  <tr key={t.id}>
                    <td className="num">{t.id}</td>
                    <td>{t.district}</td>
                    <td>{t.education_level}</td>
                    <td className="cell-sub">{(t.skills || []).map((s) => s.name).join(" · ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      </div>

      <Section
        title="Employment outcomes"
        meta={`${(employment.data || []).length} records`}
      >
        <div className="table-wrap">
          <table className="table compact">
            <thead>
              <tr>
                <th>Status</th>
                <th className="num">Trainee</th>
                <th>Role</th>
                <th>Industry</th>
                <th className="num">Salary</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {(employment.data || []).map((e) => (
                <tr key={e.id}>
                  <td>
                    <span className={`tag ${e.status === "employed" ? "tag-ok" : "tag-warn"}`}>
                      {e.status}
                    </span>
                  </td>
                  <td className="num">#{e.trainee_id}</td>
                  <td>{e.job_role || "—"}</td>
                  <td>{e.industry || "—"}</td>
                  <td className="num">{e.salary ? `₹${fmtInt(e.salary)}` : "—"}</td>
                  <td>{e.start_date || "—"}</td>
                </tr>
              ))}
              {(employment.data || []).length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">No employment records yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="micro-note">Synthetic demo data · read-only view.</p>
      </Section>
    </div>
  );
}