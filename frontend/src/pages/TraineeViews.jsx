import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import { Loading, ErrorState, Section } from "../components/PageKit.jsx";

export default function TraineeViews() {
  const self = useApi(() => api.traineeSelf(accessToken()));
  const ownId = self.data ? self.data.id : null;
  const employment = useApi(
    () => (ownId ? api.traineeEmployment(ownId, accessToken()) : Promise.reject(new Error("no id"))),
    [ownId]
  );

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

      <Section title="Your employment history" meta={`${(employment.data || []).length} records`}>
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