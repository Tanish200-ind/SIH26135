import { api } from "../api.js";
import { useApi, accessToken, fmtInt } from "../hooks.js";
import Typewriter from "../components/Typewriter.jsx";
import MetricCard from "../components/MetricCard.jsx";
import { AnimatedBar, SkillGapBar, GroupLabel } from "../components/Charts.jsx";
import { Link } from "../router.jsx";

const HEADLINE = [
  "Tracking where training leads.",
  "Finding where skills are missing.",
  "Measuring what actually works.",
];

function pct(v) {
  return v === null || v === undefined ? null : Number(v);
}

export default function DashboardPage() {
  const empl = useApi(() => api.employmentAnalytics(accessToken()));
  const gaps = useApi(() => api.skillGap(accessToken()));
  const impact = useApi(() => api.programImpact(accessToken()));

  const loading = empl.loading || gaps.loading || impact.loading;
  const allLoaded = empl.data && gaps.data && impact.data;

  if (loading) {
    return (
      <div className="loading">
        <span className="spinner" />
        Loading government dashboard…
      </div>
    );
  }

  if (!allLoaded) {
    const msg = empl.error || gaps.error || impact.error || "Could not load dashboard.";
    return (
      <div className="state-block">
        <h3>Dashboard unavailable</h3>
        <p>{msg}</p>
        <p className="muted">
          Ensure the backend is running on :8000 and that you are signed in with a
          Government (admin) account.
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="hero">
        <p className="hero-kicker">What the platform monitors</p>
        <h2 className="hero-msg">
          <Typewriter phrases={HEADLINE} />
        </h2>
        <div className="hero-rule" />
      </div>

      <EmploymentBand data={empl.data} />
      <section className="panel">
        <div className="panel-row">
          <SkillGapPanel data={gaps.data} />
          <ImpactPanel data={impact.data} />
        </div>
      </section>
      <DistrictPanel data={gaps.data} />
    </div>
  );
}

function EmploymentBand({ data }) {
  const o = data.overall;
  const headline = [
    { label: "Employment rate", value: pct(o.employment.employment_rate), suffix: "%", decimals: 1, tone: "accent" },
    { label: "Training completion", value: pct(o.completion.completion_rate), suffix: "%", decimals: 1 },
    { label: "Relevant employment", value: pct(o.relevant_employment.relevant_employment_rate), suffix: "%", decimals: 1 },
    { label: "Retention", value: pct(o.retention.retention_rate), suffix: "%", decimals: 1 },
  ];
  return (
    <section className="band">
      <div className="band-head">
        <h3>Employment outcomes</h3>
        <Link to="/employment" className="link-more">View breakdown →</Link>
      </div>
      <div className="metrics">
        {headline.map((m) => (
          <MetricCard key={m.label} label={m.label} value={m.value} suffix={m.suffix} decimals={m.decimals} tone={m.tone} />
        ))}
      </div>
      <p className="band-source">
        Computed from seeded enrolment, employment &amp; labour-demand records (docs/DATABASE.md §3.1).
      </p>
    </section>
  );
}

function SkillGapPanel({ data }) {
  const top = (data.high_demand_low_supply || []).slice(0, 5);
  const max = Math.max(1, ...top.map((s) => s.demand));
  return (
    <div className="panel-col">
      <div className="panel-head">
        <h3>Major skill gaps</h3>
        <span className="panel-count">{top.length} highlighted</span>
      </div>
      <GroupLabel meta="demand vs trained supply">High-demand / low-supply</GroupLabel>
      <div className="gaplist">
        {top.length === 0 && <p className="muted">No gaps in the current dataset.</p>}
        {top.map((s) => (
          <SkillGapBar key={s.required_skill} skill={s} max={max} />
        ))}
      </div>
      <Link to="/skill-gaps" className="link-more">Full skill-gap analysis →</Link>
    </div>
  );
}

function ImpactPanel({ data }) {
  const top = (data.ranking || []).slice(0, 6);
  const max = Math.max(1, ...top.map((r) => pct(r.composite_score) ?? 0));
  return (
    <div className="panel-col">
      <div className="panel-head">
        <h3>Programme performance</h3>
        <span className="panel-count">outcome comparison</span>
      </div>
      <GroupLabel meta="composite of employment · relevance · retention">Best-performing programmes</GroupLabel>
      <div className="hlist">
        {top.map((r) => (
          <AnimatedBar
            key={r.program_id}
            label={`#${r.program_id} · ${r.program_name}`}
            rightText={pct(r.composite_score) == null ? "no data" : `${Number(r.composite_score).toFixed(1)}%`}
            pct={pct(r.composite_score) ?? 0}
            tone={r.composite_score == null ? "muted" : "accent"}
          />
        ))}
      </div>
      <p className="micro-note">Outcome comparison only — not proof of causal impact.</p>
      <Link to="/program-impact" className="link-more">Programme impact analysis →</Link>
    </div>
  );
}

function DistrictPanel({ data }) {
  const districts = data.by_district || [];
  return (
    <section className="panel">
      <div className="panel-head">
        <h3>District-level insights</h3>
        <span className="panel-count">{districts.length} districts</span>
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>District</th>
              <th className="num">Total demand</th>
              <th className="num">Trained supply</th>
              <th className="num">Skill gap</th>
              <th className="num">Worst single gap</th>
            </tr>
          </thead>
          <tbody>
            {districts.map((d) => {
              const worst = (d.skills || [])[0];
              return (
                <tr key={d.district}>
                  <td>{d.district}</td>
                  <td className="num">{fmtInt(d.total_demand)}</td>
                  <td className="num">{fmtInt(d.total_supply)}</td>
                  <td className="num gap-positive">{fmtInt(d.total_gap)}</td>
                  <td className="num muted">{worst ? `${worst.required_skill} (+${fmtInt(worst.gap)})` : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}