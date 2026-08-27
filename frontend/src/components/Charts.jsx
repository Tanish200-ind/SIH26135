import { useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------
// AnimatedBar — a single horizontal track whose fill grows to `pct`
// on mount. CSS handles the transition (smooth, non-distracting).
// ---------------------------------------------------------------
function useMountedPct(pct) {
  const [state, setState] = useState(0);
  const done = useRef(false);
  useEffect(() => {
    if (!done.current) {
      const id = requestAnimationFrame(() => {
        setState(pct);
        done.current = true;
      });
      return () => cancelAnimationFrame(id);
    }
    return undefined;
  }, [pct]);
  return state;
}

export function AnimatedBar({ pct, label, rightText, value, tone = "ink" }) {
  const fill = useMountedPct(pct);
  return (
    <div className="hbar" title={value ? `Value: ${value}` : ""}>
      <div className="hbar-row">
        <span className="hbar-label">{label}</span>
        {rightText != null && <span className="hbar-value">{rightText}</span>}
      </div>
      <div className="hbar-track">
        <div className={`hbar-fill hbar-${tone}`} style={{ width: `${fill}%` }} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------
// SkillGapBar — shows demand (full track) vs trained supply (filled)
// for one skill. The two fill heights make demand-vs-supply visually
// comparable; the numeric labels carry the exact figures.
// ---------------------------------------------------------------
export function SkillGapBar({ skill, max }) {
  const demandPct = max ? Math.min(100, (skill.demand / max) * 100) : 0;
  const supplyPct = max ? Math.min(100, (skill.supply / max) * 100) : 0;
  const fill = useMountedPct(supplyPct);

  return (
    <div className="gapbar">
      <div className="gapbar-head">
        <span className="gapbar-label">{skill.required_skill}</span>
        <span className="gapbar-gap">gap {skill.gap >= 0 ? "+" : ""}{skill.gap}</span>
      </div>
      <div className="gapbar-track">
        <div className="gapbar-demand" style={{ transform: `scaleX(${demandPct / 100})` }} />
        <div className={`gapbar-supply ${skill.gap > 0 ? "is-gap" : ""}`} style={{ width: `${fill}%` }} />
        {/* absolute numeric endpoints */}
      </div>
      <div className="gapbar-nums">
        <span>Demand {skill.demand}</span>
        <span>Supply {skill.supply}</span>
      </div>
    </div>
  );
}

// A tiny divider / row header used to separate chart groups.
export function GroupLabel({ children, meta }) {
  return (
    <div className="group-label">
      <span>{children}</span>
      {meta ? <span className="group-meta">{meta}</span> : null}
    </div>
  );
}