import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis } from "recharts";
import { zoneFor, SERIES, BRAND } from "../lib/theme";
import RegimeBadge from "./RegimeBadge";

interface PulseCardProps {
  name: string;
  score: number;
  change1d: number;
  change1w: number;
  regime: string;
  confidence: number;
  history: number[];
  blurb?: string;
}

/** Sub-index card: serif score, zone chip, 30-day sparkline in series color. */
export default function PulseCard({
  name,
  score,
  change1d,
  change1w,
  history,
  blurb,
}: PulseCardProps) {
  const zone = zoneFor(score);
  const seriesColor =
    SERIES[name.toLowerCase() as keyof typeof SERIES] ?? BRAND.ink;
  const chartData = history.map((v, i) => ({ i, v }));

  const delta = (v: number, tag: string) => (
    <span
      className="font-data text-[11px]"
      style={{ color: v > 0 ? "#4E7325" : v < 0 ? "#A33328" : BRAND.slateFaint }}
    >
      {v > 0 ? "▲" : v < 0 ? "▼" : "—"} {v >= 0 ? "+" : ""}{v} {tag}
    </span>
  );

  return (
    <div className="mp-panel p-5 fade-in">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className="inline-block w-2.5 h-2.5 rounded-[3px]"
            style={{ backgroundColor: seriesColor }}
          />
          <h3 className="font-semibold text-[13px] tracking-wide" style={{ color: BRAND.ink }}>
            {name}
          </h3>
        </div>
        <RegimeBadge score={score} />
      </div>
      {blurb && (
        <p className="text-[11px] leading-snug mb-2" style={{ color: BRAND.slateFaint }}>
          {blurb}
        </p>
      )}

      <div className="flex items-end justify-between gap-4 mt-2">
        <span
          className="font-display num-tabular leading-none"
          style={{ fontSize: 44, fontWeight: 600, color: BRAND.ink }}
        >
          {score}
        </span>
        <div className="h-12 flex-1 min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 4, bottom: 4, left: 0, right: 0 }}>
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                cursor={{ stroke: BRAND.hairline }}
                content={({ payload }) =>
                  payload?.length ? (
                    <div className="mp-panel px-2 py-1 font-data text-[11px]" style={{ color: BRAND.ink }}>
                      {payload[0].value}
                    </div>
                  ) : null
                }
              />
              <Line type="monotone" dataKey="v" stroke={seriesColor} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex items-center gap-4 mt-3 pt-3 border-t" style={{ borderColor: BRAND.hairline }}>
        {delta(change1d, "1D")}
        {delta(change1w, "1W")}
        <span className="ml-auto font-data text-[10px]" style={{ color: BRAND.slateFaint }}>
          {zone.zone}
        </span>
      </div>
    </div>
  );
}
