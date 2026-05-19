"use client";

import { useEffect, useState } from "react";
import { clsx } from "clsx";

interface MortalityGaugeProps {
  /** 0..1 probability */
  probability: number;
  riskLevel: "LOW" | "MEDIUM" | "HIGH";
  confidenceInterval?: { lower: number; upper: number };
}

// Half-circle gauge dimensions
const W = 240;
const H = 150;
const CENTER_X = W / 2;
const CENTER_Y = 130;
const RADIUS = 100;
const STROKE = 18;

const ANIMATION_MS = 800;
const SEGMENTS = 90; // polyline resolution along the half-circle

const RISK_COLORS = {
  LOW: {
    fill: "#16a34a",
    text: "text-green-600 dark:text-green-400",
    bg: "bg-green-100 dark:bg-green-900/40",
    badge: "text-green-800 dark:text-green-300",
    glow: "from-emerald-400/30 to-emerald-600/10",
  },
  MEDIUM: {
    fill: "#f59e0b",
    text: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-100 dark:bg-amber-900/40",
    badge: "text-amber-800 dark:text-amber-300",
    glow: "from-amber-400/30 to-amber-600/10",
  },
  HIGH: {
    fill: "#dc2626",
    text: "text-red-600 dark:text-red-400",
    bg: "bg-red-100 dark:bg-red-900/40",
    badge: "text-red-800 dark:text-red-300",
    glow: "from-red-400/30 to-red-600/10",
  },
};

/**
 * Returns SVG path data for a portion of the half-circle gauge.
 * frac: 0 = far-left (9 o'clock), 0.5 = top (12 o'clock), 1 = far-right (3 o'clock).
 *
 * Builds a polyline through computed points — no arc command, no sweep-flag confusion.
 * Visual quality at 90 segments is indistinguishable from a true arc.
 */
function arcPath(startFrac: number, endFrac: number): string {
  if (endFrac <= startFrac) return "";

  const startIdx = Math.round(startFrac * SEGMENTS);
  const endIdx = Math.max(startIdx + 1, Math.round(endFrac * SEGMENTS));

  const points: string[] = [];
  for (let i = startIdx; i <= endIdx; i++) {
    const f = i / SEGMENTS;
    // Math angle goes from π (left) through 1.5π (top — sin=-1, y goes UP in SVG) to 2π (right).
    const angle = Math.PI + Math.PI * f;
    const x = CENTER_X + RADIUS * Math.cos(angle);
    const y = CENTER_Y + RADIUS * Math.sin(angle);
    points.push(`${x.toFixed(2)},${y.toFixed(2)}`);
  }

  return `M ${points[0]} L ${points.slice(1).join(" L ")}`;
}

/** Just the endpoint at a given frac — used for tick marks. */
function pointAt(frac: number) {
  const angle = Math.PI + Math.PI * frac;
  return {
    x: CENTER_X + RADIUS * Math.cos(angle),
    y: CENTER_Y + RADIUS * Math.sin(angle),
  };
}

export function MortalityGauge({
  probability,
  riskLevel,
  confidenceInterval,
}: MortalityGaugeProps) {
  const target = Math.max(0, Math.min(1, probability));
  const [animFrac, setAnimFrac] = useState(0);

  useEffect(() => {
    let frame: number;
    const start = performance.now();
    function tick(now: number) {
      const t = Math.min(1, (now - start) / ANIMATION_MS);
      const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
      setAnimFrac(target * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    }
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  const colors = RISK_COLORS[riskLevel];
  const percentText = `${Math.round(animFrac * 100)}%`;

  return (
    <div
      className="relative flex flex-col items-center"
      role="img"
      aria-label={`Mortality risk: ${Math.round(
        target * 100,
      )}%, ${riskLevel.toLowerCase()}`}
    >
      {/* Animated glow behind the gauge */}
      <div
        aria-hidden="true"
        className={clsx(
          "pointer-events-none absolute -inset-4 -z-10 rounded-full bg-gradient-radial blur-2xl",
          colors.glow,
        )}
        style={{
          background: `radial-gradient(circle at center, ${colors.fill}33, transparent 65%)`,
        }}
      />

      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        className="overflow-visible"
      >
        {/* Background track — full half-circle in slate */}
        <path
          d={arcPath(0, 1)}
          fill="none"
          className="stroke-slate-200 dark:stroke-slate-700"
          strokeWidth={STROKE}
          strokeLinecap="round"
        />

        {/* Faint color zones — green 0-10%, amber 10-30%, red 30-100% */}
        <path
          d={arcPath(0, 0.1)}
          fill="none"
          stroke="#16a34a"
          strokeOpacity="0.18"
          strokeWidth={STROKE}
        />
        <path
          d={arcPath(0.1, 0.3)}
          fill="none"
          stroke="#f59e0b"
          strokeOpacity="0.18"
          strokeWidth={STROKE}
        />
        <path
          d={arcPath(0.3, 1)}
          fill="none"
          stroke="#dc2626"
          strokeOpacity="0.18"
          strokeWidth={STROKE}
        />

        {/* Filled value arc — solid color of current risk level */}
        {animFrac > 0.001 && (
          <path
            d={arcPath(0, animFrac)}
            fill="none"
            stroke={colors.fill}
            strokeWidth={STROKE}
            strokeLinecap="round"
          />
        )}

        {/* Tick marks at 10% and 30% boundaries */}
        {[0.1, 0.3].map((frac) => {
          const p = pointAt(frac);
          // Inner and outer radii for the tick
          const angle = Math.PI + Math.PI * frac;
          const inner = {
            x: CENTER_X + (RADIUS - STROKE / 2 - 4) * Math.cos(angle),
            y: CENTER_Y + (RADIUS - STROKE / 2 - 4) * Math.sin(angle),
          };
          const outer = {
            x: CENTER_X + (RADIUS + STROKE / 2 + 4) * Math.cos(angle),
            y: CENTER_Y + (RADIUS + STROKE / 2 + 4) * Math.sin(angle),
          };
          return (
            <line
              key={frac}
              x1={inner.x}
              y1={inner.y}
              x2={outer.x}
              y2={outer.y}
              data-anchor={`${p.x}-${p.y}`}
              className="stroke-slate-400 dark:stroke-slate-500"
              strokeWidth={1}
            />
          );
        })}
      </svg>

      {/* Percentage label, sits just below the arc */}
      <div className="-mt-10 flex flex-col items-center">
        <p className={clsx("text-4xl font-bold tabular-nums", colors.text)}>
          {percentText}
        </p>
        <p className="-mt-0.5 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Mortality Risk
        </p>

        <span
          className={clsx(
            "mt-2 inline-flex items-center rounded-full px-3 py-0.5 text-xs font-semibold uppercase tracking-wider",
            colors.bg,
            colors.badge,
          )}
        >
          {riskLevel}
        </span>

        {confidenceInterval && (
          <p className="mt-1.5 text-[10px] text-slate-500 dark:text-slate-400">
            95% CI: {Math.round(confidenceInterval.lower * 100)}% –{" "}
            {Math.round(confidenceInterval.upper * 100)}%
          </p>
        )}
      </div>
    </div>
  );
}
