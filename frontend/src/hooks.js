// Small data/motion hooks used across pages.

import { useEffect, useRef, useState } from "react";
import { getToken } from "./auth";

// Fetches an API resource, tracks loading/error state, and supports a manual
// refresh() (used after login / role change).
export function useApi(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const ref = useRef(0);

  async function refresh() {
    const tick = ++ref.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await fn();
      if (tick === ref.current) setState({ data, loading: false, error: null });
    } catch (e) {
      if (tick === ref.current) setState({ data: null, loading: false, error: e.message });
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { ...state, refresh };
}

// Animates a number from 0 to `target` once the component mounts / target changes.
export function useCountUp(target, duration = 900, decimals = 0) {
  const [value, setValue] = useState(0);
  const startRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    const num = Number(target) || 0;
    if (!duration || num === 0) {
      setValue(num);
      return undefined;
    }
    const startAt = performance.now();
    const step = (now) => {
      if (startRef.current === null) startRef.current = now;
      const elapsed = now - startRef.current;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(num * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(step);
      else setValue(num);
    };
    startRef.current = null;
    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return value.toFixed(decimals);
}

// Builds a comma-grouped string from a possibly-None value.
export function fmtInt(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return Math.round(n).toLocaleString("en-IN");
}

export function accessToken() {
  return getToken();
}