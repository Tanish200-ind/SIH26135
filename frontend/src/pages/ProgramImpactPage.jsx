import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import { Loading, ErrorState, Section } from "../components/PageKit.jsx";

function num(v) {
  return v === null || v === undefined ? null : Number(v);
}

export default function ProgramImpactPage() {
  const { data, loading, error } = useApi(() => api.programImpact(accessToken()));

  if (loading) return <Loading label="Loading programme impact…" />;
  if (error || !data) return <ErrorState message={error} hint="Admin access is required." />;

  const highIds = new Set((data.high_performing || []).map((r) => r.program_id));

  return (
    <div className="stack">
      <div className="callout">
        <strong>{data.framing}</strong>
      </div>

      <Section title="Programme outcome comparison" meta={`${(data.ranking || []).length} programmes`}>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Programme</th>
                <th className="num">Enrolled</th>
                <th className="num">Completion</th>
                <th className="num">Employment</th>
                <th className="num">Relevant</th>
                <th className="num">Retention</th>
                <th className="num">Composite</th>
                <th>Band</th>
              </tr>
            </thead>
            <tbody>
              {(data.ranking || []).map((r, i) => (
                <tr key={r.program_id} className={highIds.has(r.program_id) ? "row-high" : "row-low"}>
                  <td className="num rank">{i + 1}</td>
                  <td>
                    <div className="cell-title">{r.program_name}</div>
                    <div className="cell-sub">{r.provider_name}</div>
                  </td>
                  <td className="num">{fmtInt(r.enrolled_trainees)}</td>
                  <td className="num">{num(r.completion_rate) == null ? "—" : `${Number(r.completion_rate).toFixed(1)}%`}</td>
                  <td className="num">{num(r.employment_rate) == null ? "—" : `${Number(r.employment_rate).toFixed(1)}%`}</td>
                  <td className="num">{num(r.relevant_employment_rate) == null ? "—" : `${Number(r.relevant_employment_rate).toFixed(1)}%`}</td>
                  <td className="num">{num(r.retention_rate) == null ? "—" : `${Number(r.retention_rate).toFixed(1)}%`}</td>
                  <td className="num score">
                    {num(r.composite_score) == null ? "—" : Number(r.composite_score).toFixed(1)}
                  </td>
                  <td>
                    <span className={`tag ${highIds.has(r.program_id) ? "tag-ok" : "tag-warn"}`}>
                      {highIds.has(r.program_id) ? "High-performing" : "Low-performing"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}