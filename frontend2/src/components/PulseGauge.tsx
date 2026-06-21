import { TrendingUp, TrendingDown } from "lucide-react";
import { REGIME_DEFINITIONS } from "../lib/mockData";

interface PulseGaugeProps {
  score: number;
  regime: string;
  label: string;
  change1d: number;
  change1w: number;
}

export default function PulseGauge({
  score,
  label,
  change1d,
  change1w,
}: PulseGaugeProps) {
  const size = 220;
  const stroke = 16;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const regimeDef = REGIME_DEFINITIONS.find(
    (r) => r.label.toLowerCase() === label.toLowerCase()
  );
  const color = regimeDef?.color ?? "#22C55E";

  return (
    <div className="flex flex-col items-center fade-in">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#1E293B"
            strokeWidth={stroke}
          />
          {/* Filled arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1.5s ease-out" }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-6xl font-extrabold text-white">{score}</span>
        </div>
      </div>

      {/* Regime badge */}
      <div
        className="mt-4 px-5 py-1.5 rounded-full text-sm font-semibold text-white"
        style={{ backgroundColor: color }}
      >
        {label}
      </div>

      {/* Change badges */}
      <div className="flex items-center gap-4 mt-3 text-sm">
        <div className="flex items-center gap-1">
          {change1d >= 0 ? (
            <TrendingUp size={14} className="text-emerald-400" />
          ) : (
            <TrendingDown size={14} className="text-red-400" />
          )}
          <span className={change1d >= 0 ? "text-emerald-400" : "text-red-400"}>
            {change1d >= 0 ? "+" : ""}
            {change1d} 1D
          </span>
        </div>
        <div className="flex items-center gap-1">
          {change1w >= 0 ? (
            <TrendingUp size={14} className="text-emerald-400" />
          ) : (
            <TrendingDown size={14} className="text-red-400" />
          )}
          <span className={change1w >= 0 ? "text-emerald-400" : "text-red-400"}>
            {change1w >= 0 ? "+" : ""}
            {change1w} 1W
          </span>
        </div>
      </div>
    </div>
  );
}
