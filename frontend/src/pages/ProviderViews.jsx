import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import { Loading, ErrorState, Section } from "../components/PageKit.jsx";

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