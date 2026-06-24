import { useState } from "react";
import { Globe, TrendingUp, TrendingDown } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import RegimeBadge from "../components/RegimeBadge";
import { MARKET_CONFIGS } from "../lib/mockData";
import {
  getDashboard,
  getComponents,
  getMarketComparison,
  mockDashboard,
} from "../lib/api";
import { useAsync } from "../lib/useApi";

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
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-slate-600">{entry.dataKey}:</span>
          <span className="font-medium">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function Markets() {
  const [activeMarket, setActiveMarket] = useState("sp500");
  const config = MARKET_CONFIGS.find((m) => m.id === activeMarket)!;

  const dash = useAsync(
    () => getDashboard(activeMarket),
    mockDashboard(),
    [activeMarket],
  );
  const components = useAsync(
    () => getComponents(activeMarket),
    [],
    [activeMarket],
  );
  const comparisonData = useAsync(() => getMarketComparison(), [], []);

  const subs = dash.subIndices;

  const subColors: Record<string, string> = {
    classic: "#3B82F6",
    narrative: "#A855F7",
    positioning: "#22C55E",
  };

  return (
    <div className="fade-in">
      {/* Hero */}
      <section className="py-10 md:py-14 px-4 md:px-8" style={{ backgroundColor: "#0A1628" }}>
        <div className="max-w-7xl mx-auto text-center">
          <Globe size={36} className="mx-auto mb-3 text-blue-400" />
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            Market Coverage
          </h1>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">
            Track market sentiment across major US equity indices. Each market has its own
            dedicated MarketPulse score and sub-indices.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 py-8">
        {/* Tab selector */}
        <Tabs value={activeMarket} onValueChange={setActiveMarket} className="mb-8">
          <TabsList className="grid grid-cols-2 md:grid-cols-4 w-full md:w-auto">
            {MARKET_CONFIGS.map((m) => (
              <TabsTrigger key={m.id} value={m.id} className="text-xs md:text-sm">
                {m.name}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {/* Score Display */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-center md:text-left">
              <h2 className="text-lg font-bold text-slate-800">{config.name}</h2>
              <p className="text-xs text-slate-400">{config.ticker} / {config.etf} / {config.vix}</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-4xl font-extrabold text-slate-800">{dash.composite}</div>
                <RegimeBadge regime={dash.regime} label={dash.regimeLabel} />
              </div>
            </div>
          </div>
        </div>

        {/* Three mini sub-index cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {Object.entries(subs).map(([key, data]) => (
            <div key={key} className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: subColors[key] }} />
                  <span className="text-sm font-semibold capitalize text-slate-700">{key}</span>
                </div>
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium text-white"
                  style={{ backgroundColor: subColors[key] }}
                >
                  {data.label}
                </span>
              </div>
              <div className="text-3xl font-extrabold text-slate-800 mb-2">{data.score}</div>
              <div className="flex items-center gap-3 text-xs">
                <div className="flex items-center gap-1">
                  {data.change1d >= 0 ? (
                    <TrendingUp size={12} className="text-emerald-500" />
                  ) : (
                    <TrendingDown size={12} className="text-red-500" />
                  )}
                  <span className={data.change1d >= 0 ? "text-emerald-600" : "text-red-600"}>
                    {data.change1d >= 0 ? "+" : ""}{data.change1d} 1D
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  {data.change1w >= 0 ? (
                    <TrendingUp size={12} className="text-emerald-500" />
                  ) : (
                    <TrendingDown size={12} className="text-red-500" />
                  )}
                  <span className={data.change1w >= 0 ? "text-emerald-600" : "text-red-600"}>
                    {data.change1w >= 0 ? "+" : ""}{data.change1w} 1W
                  </span>
                </div>
                <span className="text-slate-400">Conf: {data.confidence}%</span>
              </div>
            </div>
          ))}
        </div>

        {/* Multi-market comparison chart */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 mb-8">
          <h3 className="font-bold text-slate-800 text-sm mb-4">
            Multi-Market Comparison (30 Days)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={30} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="S&P 500" stroke="#3B82F6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Nasdaq 100" stroke="#A855F7" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Russell 2000" stroke="#F97316" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Dow" stroke="#22C55E" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Component comparison table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 overflow-x-auto">
          <h3 className="font-bold text-slate-800 text-sm mb-4">
            Component Comparison
          </h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Component</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Weight</TableHead>
                <TableHead>Direction</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {components.map((c) => (
                <TableRow key={c.name}>
                  <TableCell className="font-medium text-sm">{c.name}</TableCell>
                  <TableCell className="text-sm font-semibold">{c.score}</TableCell>
                  <TableCell className="text-sm">{(c.weight * 100).toFixed(1)}%</TableCell>
                  <TableCell>
                    <span
                      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize"
                      style={{
                        backgroundColor: c.direction === "bullish" ? "#22C55E18" : c.direction === "bearish" ? "#DC262618" : "#6B728018",
                        color: c.direction === "bullish" ? "#22C55E" : c.direction === "bearish" ? "#DC2626" : "#6B7280",
                      }}
                    >
                      {c.direction}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-slate-500">{c.description}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}
