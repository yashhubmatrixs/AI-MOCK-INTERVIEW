import { useEffect, useState } from "react";

// Visual pacing cue only - it never force-submits, it just turns red when
// time is short so the candidate can wrap up.
export default function Timer({ seconds = 180, resetKey }) {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    setRemaining(seconds);
    const id = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(id);
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [seconds, resetKey]);

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");
  const isLow = remaining <= 30;

  return (
    <div className={`timer ${isLow ? "is-low" : ""}`}>
      {mm}:{ss}
    </div>
  );
}
