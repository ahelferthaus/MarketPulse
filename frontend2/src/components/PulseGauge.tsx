/**
 * The MarketPulse barometer — the platform's signature instrument.
 *
 * A semicircular precision dial: five zone segments (the MP-1…MP-5 framework,
 * drawn to the real asymmetric band boundaries), an etched tick ring, and a
 * gold needle on deep navy. The score is the headline; the dial is the proof.
 */
import { ZONES, zoneFor, BRAND } from "../lib/theme";

interface PulseGaugeProps {
  score: number;
  regime: string;
  label: string;
  change1d: number;
  change1w: number;
}

const CX = 280;
const CY = 268;
const R_ARC = 216;        // zone-arc centerline radius
const ARC_W = 30;         // zone-arc stroke width
const R_TICK_OUT = 244;   // tick ring outer radius
const GAP_DEG = 1.4;      // angular gap between zone segments

/** score 0..100 → angle in degrees, 180 (left) → 0 (right). */
const angleOf = (s: number) => 180 - (s / 100) * 180;

const rad = (deg: number) => (deg * Math.PI) / 180;

function polar(cx: number, cy: number, r: number, deg: number) {
  return { x: cx + r * Math.cos(rad(deg)), y: cy - r * Math.sin(rad(deg)) };
}

/** SVG arc path along the dial from score a → b at radius r. */
function arcPath(a: number, b: number, r: number) {
  const p1 = polar(CX, CY, r, angleOf(a));
  const p2 = polar(CX, CY, r, angleOf(b));
  return `M ${p1.x.toFixed(2)} ${p1.y.toFixed(2)} A ${r} ${r} 0 0 1 ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`;
}

export default function PulseGauge({
  score,
  change1d,
  change1w,
}: PulseGaugeProps) {
  const zone = zoneFor(score);
  const needleDeg = angleOf(score);

  // minor ticks every 2 pts, major every 10
  const ticks = [];
  for (let s = 0; s <= 100; s += 2) {
    const major = s % 10 === 0;
    const a = angleOf(s);
    const o = polar(CX, CY, R_TICK_OUT, a);
    const i = polar(CX, CY, R_TICK_OUT - (major ? 13 : 7), a);
    ticks.push(
      <line
        key={s}
        x1={o.x} y1={o.y} x2={i.x} y2={i.y}
        stroke={major ? "rgba(255,255,255,0.5)" : "rgba(255,255,255,0.22)"}
        strokeWidth={major ? 1.6 : 1}
      />,
    );
  }

  const numerals = [0, 20, 40, 60, 80, 100].map((s) => {
    const p = polar(CX, CY, R_TICK_OUT + 15, angleOf(s));
    return (
      <text
        key={s}
        x={p.x} y={p.y + 4}
        textAnchor="middle"
        className="font-data"
        fontSize="11"
        fill="rgba(255,255,255,0.55)"
      >
        {s}
      </text>
    );
  });

  const delta = (v: number, tag: string) => (
    <tspan fill={v >= 0 ? "#8FBF6A" : "#E08A80"}>
      {v >= 0 ? "▲" : "▼"} {v >= 0 ? "+" : ""}{v} {tag}
    </tspan>
  );

  return (
    <div className="fade-in" role="img"
         aria-label={`MarketPulse composite ${score} of 100 — ${zone.zone} ${zone.label}`}>
      <svg viewBox="0 0 560 330" className="w-full max-w-[560px]">
        {/* etched tick ring */}
        {ticks}
        {numerals}

        {/* zone arc — five segments with surface gaps, real band boundaries */}
        {ZONES.map((z) => {
          const a = z.min + (z.min === 0 ? 0 : GAP_DEG / 1.8);
          const b = z.max - (z.max === 100 ? 0 : GAP_DEG / 1.8);
          const active = z.id === zone.id;
          return (
            <path
              key={z.id}
              d={arcPath(a, b, R_ARC)}
              fill="none"
              stroke={z.onNavy}
              strokeWidth={ARC_W}
              opacity={active ? 1 : 0.4}
            />
          );
        })}

        {/* annular needle — sweeps the outer ring only, never the numeral */}
        <g
          style={{
            transform: `rotate(${90 - needleDeg}deg)`,
            transformOrigin: `${CX}px ${CY}px`,
            transition: "transform 1.1s cubic-bezier(.25,.7,.3,1)",
          }}
        >
          <polygon
            points={`${CX - 3.5},${CY - 124} ${CX + 3.5},${CY - 124} ${CX + 1},${CY - 196} ${CX - 1},${CY - 196}`}
            fill={BRAND.gold}
          />
          <circle cx={CX} cy={CY - 124} r="4.5" fill={BRAND.navy950} stroke={BRAND.gold} strokeWidth="2" />
        </g>

        {/* score numeral + regime plate — inside the needle's clear radius */}
        <text
          x={CX} y={CY - 50}
          textAnchor="middle"
          className="font-display num-tabular"
          fontSize="76"
          fontWeight="600"
          fill="#FFFFFF"
        >
          {score}
        </text>
        <g>
          <rect
            x={CX - 76} y={CY - 36}
            width="152" height="26" rx="13"
            fill={zone.onNavy}
          />
          <text
            x={CX} y={CY - 18.5}
            textAnchor="middle"
            fontSize="12.5"
            fontWeight="700"
            letterSpacing="1.6"
            fill="#FFFFFF"
          >
            {zone.label.toUpperCase()}
          </text>
        </g>
        <text x={CX} y={CY + 42} textAnchor="middle" className="font-data" fontSize="13">
          {delta(change1d, "1D")}
          <tspan fill="rgba(255,255,255,0.25)">   ·   </tspan>
          {delta(change1w, "1W")}
        </text>

        {/* dial base line */}
        <line
          x1={CX - 258} y1={CY + 20} x2={CX + 258} y2={CY + 20}
          stroke="rgba(200,169,81,0.35)" strokeWidth="1"
        />
        <text x={CX - 258} y={CY + 38} className="font-data" fontSize="10" fill="rgba(255,255,255,0.4)">
          0 — RISK-OFF
        </text>
        <text x={CX + 258} y={CY + 38} textAnchor="end" className="font-data" fontSize="10" fill="rgba(255,255,255,0.4)">
          RISK-ON — 100
        </text>
      </svg>
    </div>
  );
}
