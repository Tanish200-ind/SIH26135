import { useEffect, useState } from "react";

// Cycles a set of contextual messages with a typewriter effect.
// Purposeful motion: draws the analyst's eye to the active theme without
// distracting from the data around it.
export default function Typewriter({ phrases, typeMs = 55, deleteMs = 26, pauseMs = 1400 }) {
  const [text, setText] = useState("");
  const [idx, setIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!phrases.length) return undefined;
    const full = phrases[idx];
    let timer;
    if (!deleting && text === full) {
      timer = setTimeout(() => setDeleting(true), pauseMs);
    } else if (deleting && text === "") {
      setDeleting(false);
      setIdx((i) => (i + 1) % phrases.length);
    } else {
      const step = deleting ? -1 : 1;
      const speed = deleting ? deleteMs : typeMs;
      timer = setTimeout(() => setText(full.slice(0, text.length + step)), speed);
    }
    return () => clearTimeout(timer);
  }, [text, deleting, idx, phrases, typeMs, deleteMs, pauseMs]);

  return (
    <span className="typewriter" aria-live="polite">
      {text}
      <span className="tw-caret" aria-hidden="true" />
    </span>
  );
}