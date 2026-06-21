import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { MOCK_HISTORY } from "../lib/mockData";

const zoneLines = [20, 40, 60, 80];

const zoneColors: Record<number, string> = {
  20: "rgba(220,38,38,0.15)",
  40: "rgba(249,115,22,0.15)",
  60: "rgba(107,114,128,0.15)",
  80: "rgba(34,197,94,0.15)",
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string; color: string }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-lg text-xs">
      <p className="font-semibold text-slate-700 mb-1">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 py-0.5">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-slate-600 capitalize">{entry.dataKey}:</span>
          <span className="font-medium text-slate-800">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function StackedPulseChart() {
  const data = MOCK_HISTORY;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 fade-in">
      <h3 className="font-bold text-slate-800 text-base mb-4">
        90-Day Pulse History
      </h3>

      <div className="space-y-4">
        {/* S&P 500 */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">S&P 500</span>
          </div>
          <ResponsiveContainer width="100%" height={130}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={45} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="sp500"
                stroke="#94A3B8"
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Classic */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">Classic</span>
          </div>
          <ResponsiveContainer width="100%" height={130}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={30} />
              <Tooltip content={<CustomTooltip />} />
              {zoneLines.map((z) => (
                <ReferenceLine
                  key={z}
                  y={z}
                  stroke={zoneColors[z]?.replace("0.15", "0.4") ?? "#ccc"}
                  strokeDasharray="3 3"
                  strokeWidth={1}
                />
              ))}
              <Area
                type="monotone"
                dataKey="classic"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.15}
                strokeWidth={1.5}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Narrative */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">Narrative</span>
          </div>
          <ResponsiveContainer width="100%" height={130}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={30} />
              <Tooltip content={<CustomTooltip />} />
              {zoneLines.map((z) => (
                <ReferenceLine
                  key={z}
                  y={z}
                  stroke={zoneColors[z]?.replace("0.15", "0.4") ?? "#ccc"}
                  strokeDasharray="3 3"
                  strokeWidth={1}
                />
              ))}
              <Area
                type="monotone"
                dataKey="narrative"
                stroke="#A855F7"
                fill="#A855F7"
                fillOpacity={0.15}
                strokeWidth={1.5}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Positioning */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">Positioning</span>
          </div>
          <ResponsiveContainer width="100%" height={130}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={30} />
              <Tooltip content={<CustomTooltip />} />
              {zoneLines.map((z) => (
                <ReferenceLine
                  key={z}
                  y={z}
                  stroke={zoneColors[z]?.replace("0.15", "0.4") ?? "#ccc"}
                  strokeDasharray="3 3"
                  strokeWidth={1}
                />
              ))}
              <Area
                type="monotone"
                dataKey="positioning"
                stroke="#22C55E"
                fill="#22C55E"
                fillOpacity={0.15}
                strokeWidth={1.5}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Zone Legend */}
      <div className="flex items-center justify-center gap-4 mt-4 text-xs text-slate-500">
        <span>Zone Reference:</span>
        {zoneLines.map((z) => (
          <div key={z} className="flex items-center gap-1">
            <span
              className="w-3 h-0.5 rounded"
              style={{
                backgroundColor:
                  zoneColors[z]?.replace("0.15", "0.6") ?? "#ccc",
              }}
            />
            <span>{z}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
