import { useCountUp } from "../hooks.js";

// Animated metric value. `decimals` controls rounding (percent uses 1-2 dp,
// counts use 0). Falls back gracefully to the formatted number when idle.
export default function CountUp({ value, decimals = 0, suffix = "", prefix = "", duration }) {
  const rendered = useCountUp(value, duration, decimals);
  return (
    <span className="countup">
      {prefix}
      {rendered}
      {suffix}
    </span>
  );
}