import { useState } from "react";
import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import { Loading, ErrorState, Section } from "../components/PageKit.jsx";

const ENROLLMENT_TAG = {
  enrolled: "tag-info",
  completed: "tag-ok",
  dropped: "tag-warn",
};

// Trainee workflow: browse the catalogue and enrol in an active programme.
// Ownership comes entirely from the JWT on the server — nothing here sends ids.
function ProgramCatalogue({ available, busyId, onEnroll }) {
  return (
    <Section title="Available programmes" meta={`${available.length} in catalog`}>
      <div className="catalog-list">
        {available.map((p) => (
          <div className="catalog-item" key={p.id}>
            <div className="catalog-main">
              <div className="cell-title">{p.name}</div>
              <div className="cell-sub">
                {p.provider_name} · {p.duration_weeks} weeks ·{" "}
                {(p.skills || []).map((s) => s.name).join(" · ") || "—"}
              </div>
            </div>
            <div className="catalog-action">
              {p.enrolled ? (
                <span className={`tag ${ENROLLMENT_TAG[p.enrollment_status] || ""}`}>
                  Enrolled
                </span>
              ) : p.status === "closed" ? (
                <span className="tag tag-muted">Closed</span>
              ) : (
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  disabled={busyId !== null}
                  onClick={() => onEnroll(p.id)}
                >
                  {busyId === p.id ? "Enrolling…" : "Enroll"}
                </button>
              )}
            </div>
          </div>
        ))}
        {available.length === 0 && (
          <p className="muted">No programmes are available yet.</p>
        )}
      </div>
      <p className="micro-note">Synthetic demo data · enrollment applies to your own account.</p>
    </Section>
  );
}

export default function TraineeViews() {
  const self = useApi(() => api.traineeSelf(accessToken()));
  const ownId = self.data ? self.data.id : null;
  const employment = useApi(
    () => (ownId ? api.traineeEmployment(ownId, accessToken()) : Promise.reject(new Error("no id"))),
    [ownId]
  );

  // Enrollment state is fetched after the profile resolves and refreshed
  // whenever an enroll call succeeds.
  const [enrollTick, setEnrollTick] = useState(0);
  const myEnrollments = useApi(() => api.myEnrollments(accessToken()), [enrollTick]);
  const available = useApi(() => api.availablePrograms(accessToken()), [enrollTick]);

  const [busyId, setBusyId] = useState(null);
  const [flash, setFlash] = useState(null);
  const [error, setError] = useState(null);

  async function handleEnroll(programId) {
    setBusyId(programId);
    setFlash(null);
    setError(null);
    try {
      await api.enroll(programId, accessToken());
      setFlash("You are now enrolled.");
      setEnrollTick((x) => x + 1); // refreshes both catalogue and enrolment list
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  if (self.loading) return <Loading label="Loading your profile…" />;
  if (self.error || !self.data) return <ErrorState message={self.error} hint="Trainee access is required." />;

  const t = self.data;

  return (
    <div className="stack">
      <Section title="Your profile" meta={`Trainee #${t.id}`}>
        <div className="profile-grid">
          <div className="profile-item">
            <span className="profile-key">District</span>
            <span className="profile-value">{t.district}</span>
          </div>
          <div className="profile-item">
            <span className="profile-key">Education</span>
            <span className="profile-value">{t.education_level}</span>
          </div>
          <div className="profile-item">
            <span className="profile-key">Skills recorded</span>
            <span className="profile-value">{(t.skills || []).map((s) => s.name).join(", ") || "—"}</span>
          </div>
        </div>
      </Section>

      <Section
        title="Your enrolments"
        meta={`${(myEnrollments.data || []).length} programme(s)`}
      >
        {myEnrollments.loading && <Loading label="Loading your enrolments…" />}
        {!myEnrollments.loading && (
          <>
            {flash && !error && <p className="wf-flash">{flash}</p>}
            {error && <p className="wf-error">{error}</p>}
            <div className="table-wrap">
              <table className="table compact">
                <thead>
                  <tr>
                    <th>Programme</th>
                    <th>Provider</th>
                    <th className="num">Duration (wk)</th>
                    <th>Status</th>
                    <th>Certification</th>
                    <th>Enrolled on</th>
                  </tr>
                </thead>
                <tbody>
                  {(myEnrollments.data || []).map((e) => (
                    <tr key={e.id}>
                      <td>{e.program ? e.program.name : `#${e.program_id}`}</td>
                      <td className="cell-sub">{e.program ? e.program.provider_name : "—"}</td>
                      <td className="num">{e.program ? e.program.duration_weeks : "—"}</td>
                      <td>
                        <span className={`tag ${ENROLLMENT_TAG[e.completion_status] || ""}`}>
                          {e.completion_status}
                        </span>
                      </td>
                      <td className="cell-sub">{e.certification_status}</td>
                      <td>{e.enrolled_date}</td>
                    </tr>
                  ))}
                  {(myEnrollments.data || []).length === 0 && (
                    <tr>
                      <td colSpan={6} className="muted">
                        Not enrolled yet — pick a programme below.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Section>

      {available.loading && <Loading label="Loading available programmes…" />}
      {!available.loading && !available.error && available.data && (
        <ProgramCatalogue
          available={available.data}
          busyId={busyId}
          onEnroll={handleEnroll}
        />
      )}

      <Section
        title="Your employment history"
        meta={`${(employment.data || []).length} records`}
      >
        {employment.loading && <Loading label="Loading your employment…" />}
        {!employment.loading && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Role</th>
                  <th>Industry</th>
                  <th className="num">Salary</th>
                  <th>Started</th>
                  <th>Currently employed</th>
                </tr>
              </thead>
              <tbody>
                {(employment.data || []).map((e) => (
                  <tr key={e.id}>
                    <td>
                      <span className={`tag ${e.status === "employed" ? "tag-ok" : "tag-warn"}`}>{e.status}</span>
                    </td>
                    <td>{e.job_role || "—"}</td>
                    <td>{e.industry || "—"}</td>
                    <td className="num">{e.salary ? `₹${fmtInt(e.salary)}` : "—"}</td>
                    <td>{e.start_date || "—"}</td>
                    <td>{e.still_employed ? "Yes" : "No"}</td>
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
        )}
      </Section>
    </div>
  );
}
