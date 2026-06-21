import { Info, TrendingUp, TrendingDown } from "lucide-react";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { REGIME_DEFINITIONS } from "../lib/mockData";
import SourceQualityBadge from "./SourceQualityBadge";

interface PulseCardProps {
  name: string;
  score: number;
  change1d: number;
  change1w: number;
  regime: string;
  confidence: number;
  history: number[];
}

export default function PulseCard({
  name,
  score,
  change1d,
  change1w,
  regime,
  confidence,
  history,
}: PulseCardProps) {
  const regimeDef = REGIME_DEFINITIONS.find(
    (r) => r.label.toLowerCase() === regime.toLowerCase()
  );
  const color = regimeDef?.color ?? "#22C55E";

  const chartData = history.map((v, i) => ({ i, v }));

  return (
    <div
      className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 fade-in"
    >
      {/* Title row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <h3 className="font-semibold text-slate-800 text-sm">{name}</h3>
          <span className="text-slate-400 cursor-help" title={`${name} Index details`}>
            <Info size={14} />
          </span>
        </div>
        <SourceQualityBadge confidence={confidence} />
      </div>

      {/* Score */}
      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-4xl font-extrabold" style={{ color }}>
          {score}
        </span>
        <span
          className="text-xs px-2 py-0.5 rounded-full text-white font-medium"
          style={{ backgroundColor: color }}
        >
          {regime}
        </span>
      </div>

      {/* Mini sparkline */}
      <div className="h-10 mb-3">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <Tooltip
              content={({ payload }) => {
                if (!payload?.length) return null;
                return (
                  <div className="bg-slate-800 text-white text-xs px-2 py-1 rounded">
                    {payload[0].value}
                  </div>
                );
              }}
            />
            <Line
              type="monotone"
              dataKey="v"
              stroke={color}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Change badges */}
      <div className="flex items-center gap-3 text-xs">
        <div className="flex items-center gap-1">
          {change1d >= 0 ? (
            <TrendingUp size={12} className="text-emerald-500" />
          ) : (
            <TrendingDown size={12} className="text-red-500" />
          )}
          <span className={change1d >= 0 ? "text-emerald-600" : "text-red-600"}>
            {change1d >= 0 ? "+" : ""}
            {change1d} 1D
          </span>
        </div>
        <div className="flex items-center gap-1">
          {change1w >= 0 ? (
            <TrendingUp size={12} className="text-emerald-500" />
          ) : (
            <TrendingDown size={12} className="text-red-500" />
          )}
          <span className={change1w >= 0 ? "text-emerald-600" : "text-red-600"}>
            {change1w >= 0 ? "+" : ""}
            {change1w} 1W
          </span>
        </div>
      </div>
    </div>
  );
}
