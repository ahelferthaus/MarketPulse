/**
 * Pulse history — one consolidated panel.
 *
 * The composite line reads against the five MP zone bands (drawn to the real
 * asymmetric boundaries). Sub-indices are optional thin overlays, off by
 * default, toggled from the legend. One axis, one chart.
 */
import { useMemo, useState } from "react";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
import { MOCK_HISTORY, type HistoryPoint } from "../lib/mockData";
import { ZONES, SERIES, SERIES_LABELS, BRAND, zoneFor } from "../lib/theme";

type SeriesKey = keyof typeof SERIES;
const SERIES_KEYS = Object.keys(SERIES) as SeriesKey[];
const RANGES = [30, 60, 90] as const;

interface TooltipRow {
  value: number;
  dataKey: string;
  color?: string;
}

function PulseTooltip({ active, payload, label }: {
  active?: boolean; payload?: TooltipRow[]; label?: string;
}) {
  if (!active || !payload?.length) return null;
  const composite = payload.find((p) => p.dataKey === "composite");
  return (
    <div className="mp-panel px-3 py-2 shadow-md">
      <p className="font-data text-[11px] mb-1" style={{ color: BRAND.slateFaint }}>{label}</p>
      {payload.map((row) => (
        <div key={row.dataKey} className="flex items-center gap-2 py-px text-[12px]">
          <span
            aria-hidden
            className="inline-block w-2.5 h-2.5 rounded-[3px]"
            style={{
              backgroundColor:
                row.dataKey === "composite" ? BRAND.ink : SERIES[row.dataKey as SeriesKey],
            }}
          />
          <span style={{ color: BRAND.slate }}>
            {row.dataKey === "composite" ? "Composite" : SERIES_LABELS[row.dataKey as SeriesKey]}
          </span>
          <span className="font-data ml-auto pl-4" style={{ color: BRAND.ink }}>{row.value}</span>
        </div>
      ))}
      {composite && (
        <p className="text-[10px] mt-1 pt-1 border-t" style={{ color: BRAND.slateFaint, borderColor: BRAND.hairline }}>
          {zoneFor(composite.value).zone} · {zoneFor(composite.value).label}
        </p>
      )}
    </div>
  );
}

interface StackedPulseChartProps {
  data?: HistoryPoint[];
}

export default function StackedPulseChart({ data = MOCK_HISTORY }: StackedPulseChartProps) {
  const [range, setRange] = useState<(typeof RANGES)[number]>(90);
  const [visible, setVisible] = useState<Record<SeriesKey, boolean>>({
    classic: false,
    narrative: false,
    positioning: false,
  });

  const sliced = useMemo(() => data.slice(-range), [data, range]);

  const toggle = (k: SeriesKey) =>
    setVisible((v) => ({ ...v, [k]: !v[k] }));

  return (
    <div className="mp-panel p-5 md:p-6 fade-in">
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div>
          <div className="mp-eyebrow">Pulse history</div>
          <h3 className="font-display text-lg mt-0.5" style={{ color: BRAND.ink }}>
            Composite against the five zones
          </h3>
        </div>

        {/* range + series controls, one row */}
        <div className="ml-auto flex items-center gap-4">
          <div className="flex items-center gap-1" role="group" aria-label="History range">
            {RANGES.map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className="px-2.5 py-1 rounded-md font-data text-[11px] transition-colors"
                style={
                  range === r
                    ? { backgroundColor: BRAND.navy900, color: "#fff" }
                    : { color: BRAND.slate }
                }
              >
                {r}D
              </button>
            ))}
          </div>
          <div className="hidden sm:flex items-center gap-2">
            {SERIES_KEYS.map((k) => (
              <button
                key={k}
                onClick={() => toggle(k)}
                aria-pressed={visible[k]}
                className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium transition-opacity"
                style={{ color: BRAND.slate, opacity: visible[k] ? 1 : 0.45 }}
              >
                <span
                  aria-hidden
                  className="inline-block w-2.5 h-2.5 rounded-[3px]"
                  style={{ backgroundColor: SERIES[k] }}
                />
                {SERIES_LABELS[k]}
              </button>
            ))}
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={sliced} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
          {/* the five zones as quiet horizontal bands */}
          {ZONES.map((z) => (
            <ReferenceArea
              key={z.id}
              y1={z.min}
              y2={z.max}
              fill={z.onPaper}
              fillOpacity={0.06}
              stroke="none"
            />
          ))}
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: BRAND.slateFaint, fontFamily: "IBM Plex Mono" }}
            tickLine={false}
            axisLine={{ stroke: BRAND.hairline }}
            minTickGap={42}
          />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 24, 44, 55, 75, 100]}
            tick={{ fontSize: 10, fill: BRAND.slateFaint, fontFamily: "IBM Plex Mono" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<PulseTooltip />} cursor={{ stroke: BRAND.slateFaint, strokeDasharray: "3 3" }} />
          {SERIES_KEYS.filter((k) => visible[k]).map((k) => (
            <Line
              key={k}
              type="monotone"
              dataKey={k}
              stroke={SERIES[k]}
              strokeWidth={1.6}
              dot={false}
            />
          ))}
          <Line
            type="monotone"
            dataKey="composite"
            stroke={BRAND.ink}
            strokeWidth={2.2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* zone key — the y-axis tick positions are the real band boundaries */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 pt-3 border-t" style={{ borderColor: BRAND.hairline }}>
        {ZONES.map((z) => (
          <div key={z.id} className="flex items-center gap-1.5 text-[11px]" style={{ color: BRAND.slate }}>
            <span aria-hidden className="inline-block w-3 h-2 rounded-[2px]" style={{ backgroundColor: z.onPaper, opacity: 0.5 }} />
            <span className="font-data">{z.zone}</span> {z.label}
          </div>
        ))}
        <span className="ml-auto text-[11px]" style={{ color: BRAND.slateFaint }}>
          Band edges mark the real zone boundaries (24 / 44 / 55 / 75)
        </span>
      </div>
    </div>
  );
}
