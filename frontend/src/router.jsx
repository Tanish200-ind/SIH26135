// Minimal dependency-free hash router.
// Routes are expressed as a list of {path, element, guard?} in App.jsx. A tiny
// listener keeps the current location in sync with window.location.hash.
import { createElement, useEffect, useState } from "react";

function parseHash() {
  const raw = window.location.hash.replace(/^#/, "") || "/";
  const [path, query = ""] = raw.split("?");
  return { path: path || "/", params: new URLSearchParams(query) };
}

export function useLocation() {
  const [loc, setLoc] = useState(parseHash);
  useEffect(() => {
    const onChange = () => {
      setLoc(parseHash());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return loc;
}

export function navigate(to) {
  window.location.hash = to;
}

export function Link({ to, children, className, ...rest }) {
  return createElement(
    "a",
    {
      href: `#${to}`,
      className,
      ...rest,
    },
    children
  );
}

export function Router({ routes, fallback }) {
  const { path } = useLocation();
  // Exact match first, then prefix match (for /analytics/employment entries).
  const exact = routes.find((r) => r.path === path);
  const matched =
    exact ||
    routes.find((r) => r.path !== "/" && path.startsWith(`${r.path}/`)) ||
    null;
  const route = matched || routes.find((r) => r.path === "/") || null;
  if (!route) return typeof fallback === "function" ? fallback(null) : fallback;
  return route.element;
}