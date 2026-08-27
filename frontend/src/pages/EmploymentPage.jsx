import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import { Loading, ErrorState, Section, StatBand } from "../components/PageKit.jsx";

function num(v) {
  return v === null || v === undefined ? null : Number(v);
}

export default function EmploymentPage() {
  const { data, loading, error } = useApi(() => api.employmentAnalytics(accessToken()));

  if (loading) return <Loading label="Loading employment outcomes…" />;
  if (error || !data) return <ErrorState message={error} hint="Admin access is required." />;

  const o = data.overall;
  const items = [
    { label: "Employment rate", value: num(o.employment.employment_rate), suffix: "%", decimals: 1, tone: "accent" },
    { label: "Training completion", value: num(o.completion.completion_rate), suffix: "%", decimals: 1 },
    { label: "Relevant employment", value: num(o.relevant_employment.relevant_employment_rate), suffix: "%", decimals: 1 },
    { label: "Retention (N mo)", value: num(o.retention.retention_rate), suffix: "%", decimals: 1 },
  ];

  return (
    <div className="stack">
      <StatBand items={items} />
      <div className="micro-note">
        As-of {data.as_of} · retention window {data.retention_months} months ·
        formulas per docs/DATABASE.md §3.1
      </div>

      <Section title="By programme" meta={`${data.by_program.length} programmes`}>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Programme</th>
                <th className="num">Enrolled</th>
                <th className="num">Completed</th>
                <th className="num">Completion</th>
                <th className="num">Employed</th>
                <th className="num">Employment</th>
                <th className="num">Relevant</th>
                <th className="num">Retention</th>
              </tr>
            </thead>
            <tbody>
              {data.by_program.map((p) => (
                <tr key={p.program_id}>
                  <td>
                    <div className="cell-title">{p.program_name}</div>
                    <div className="cell-sub">{p.provider_name}</div>
                  </td>
                  <td className="num">{fmtInt(p.enrolled_trainees)}</td>
                  <td className="num">{p.completed_enrollments}/{p.total_enrollments}</td>
                  <td className="num">{num(p.completion_rate) == null ? "—" : `${Number(p.completion_rate).toFixed(1)}%`}</td>
                  <td className="num">{p.employed}/{p.available}</td>
                  <td className="num">{num(p.employment_rate) == null ? "—" : `${Number(p.employment_rate).toFixed(1)}%`}</td>
                  <td className="num">{num(p.relevant_employment_rate) == null ? "—" : `${Number(p.relevant_employment_rate).toFixed(1)}%`}</td>
                  <td className="num">{num(p.retention_rate) == null ? "—" : `${Number(p.retention_rate).toFixed(1)}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}