import CountUp from "./CountUp.jsx";

// A labeled value block for the dashboard stat bands.
// `raw` can be null -> MetricCard renders "No data" instead of animating.
export default function MetricCard({ label, value, suffix = "", decimals = 0, note, tone = "ink" }) {
  const hasValue = value !== null && value !== undefined && Number.isFinite(Number(value));
  return (
    <div className={`metric metric-${tone}`}>
      <span className="metric-label">{label}</span>
      <span className="metric-value">
        {hasValue ? <CountUp value={value} suffix={suffix} decimals={decimals} /> : "No data"}
      </span>
      {note ? <span className="metric-note">{note}</span> : null}
    </div>
  );
}