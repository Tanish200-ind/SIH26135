import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import { Loading, ErrorState, Section } from "../components/PageKit.jsx";
import { SkillGapBar, GroupLabel } from "../components/Charts.jsx";

export default function SkillGapPage() {
  const { data, loading, error } = useApi(() => api.skillGap(accessToken()));

  if (loading) return <Loading label="Loading skill-gap analysis…" />;
  if (error || !data) return <ErrorState message={error} hint="Admin access is required." />;

  const flagged = data.high_demand_low_supply || [];
  const max = Math.max(1, ...flagged.map((s) => s.demand));

  return (
    <div className="stack">
      <Section title="High-demand / low-supply skills" meta={`${flagged.length} flagged`}>
        <div className="micro-note">
          Supply counts trained trainees at proficiency ≥ {data.proficiency_threshold} ·
          gap = demand − trained supply (docs/DATABASE.md §3.2).
        </div>
        <GroupLabel>Ranked by gap</GroupLabel>
        <div className="gaplist">
          {flagged.length === 0 && <p className="muted">No skill gaps in the current dataset.</p>}
          {flagged.map((s) => (
            <SkillGapBar key={s.required_skill} skill={s} max={max} />
          ))}
        </div>
      </Section>

      <Section title="Full skill demand vs supply" meta={`${(data.skills || []).length} skills`}>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Skill</th>
                <th className="num">Demand</th>
                <th className="num">Supply</th>
                <th className="num">Gap</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(data.skills || []).map((s) => (
                <tr key={s.required_skill}>
                  <td>{s.required_skill}</td>
                  <td className="num">{fmtInt(s.demand)}</td>
                  <td className="num">{fmtInt(s.supply)}</td>
                  <td className={`num ${s.gap > 0 ? "gap-positive" : "gap-neutral"}`}>
                    {s.gap > 0 ? `+${fmtInt(s.gap)}` : fmtInt(s.gap)}
                  </td>
                  <td>
                    <span className={`tag ${s.gap > 0 ? "tag-warn" : "tag-ok"}`}>
                      {s.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="District-level gaps" meta={`${(data.by_district || []).length} districts`}>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>District</th>
                <th className="num">Total demand</th>
                <th className="num">Trained supply</th>
                <th className="num">Total gap</th>
                <th>Top skills</th>
              </tr>
            </thead>
            <tbody>
              {(data.by_district || []).map((d) => (
                <tr key={d.district}>
                  <td>{d.district}</td>
                  <td className="num">{fmtInt(d.total_demand)}</td>
                  <td className="num">{fmtInt(d.total_supply)}</td>
                  <td className="num gap-positive">{fmtInt(d.total_gap)}</td>
                  <td className="cell-sub">
                    {(d.skills || []).slice(0, 3).map((s) => s.required_skill).join(" · ") || "—"}
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