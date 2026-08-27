// Small shared building blocks used by the detail pages.
import MetricCard from "./MetricCard.jsx";

export function Loading({ label = "Loading…" }) {
  return (
    <div className="loading">
      <span className="spinner" />
      {label}
    </div>
  );
}

export function ErrorState({ message, hint }) {
  return (
    <div className="state-block">
      <h3>This view is unavailable</h3>
      <p>{message || "The data could not be loaded."}</p>
      {hint && <p className="muted">{hint}</p>}
    </div>
  );
}

export function Section({ title, meta, action, children }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h3>{title}</h3>
        <span className="panel-head-right">
          {meta != null && <span className="panel-count">{meta}</span>}
          {action}
        </span>
      </div>
      {children}
    </section>
  );
}

export function StatBand({ items }) {
  return (
    <section className="band">
      <div className="metrics">
        {items.map((it) => (
          <MetricCard key={it.label} {...it} />
        ))}
      </div>
    </section>
  );
}