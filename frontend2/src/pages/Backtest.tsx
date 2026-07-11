import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FORWARD_RETURNS, REGIME_TRANSITIONS } from "../lib/mockData";
import { getForwardReturns } from "../lib/api";
import { useAsync } from "../lib/useApi";

interface TooltipPayloadItem {
  value: number;
  dataKey: string;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
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
          <span className="text-slate-600">{entry.dataKey}:</span>
          <span className="font-medium">{entry.value}%</span>
        </div>
      ))}
    </div>
  );
}

export default function Backtest() {
  const forwardReturns = useAsync(
    () => getForwardReturns("sp500"),
    FORWARD_RETURNS,
    [],
  );

  // Regime distribution data
  const regimeDist = forwardReturns.map((r) => ({
    name: r.regime.split(" ")[0],
    label: r.regime,
    occurrences: r.occurrences,
    color: r.color,
  }));

  return (
    <div className="fade-in">
      {/* Header */}
      <section className="py-8 md:py-10 px-4 md:px-8" style={{ backgroundColor: "#0B2240" }}>
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="font-display text-2xl md:text-3xl font-semibold text-white mb-2">
            Historical Analysis
          </h1>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">
            Backtested forward returns by market regime. Use with caution.
          </p>
        </div>
      </section>

      {/* Disclaimer Banner */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pt-6">
        <div
          className="rounded-xl p-4 border-l-4"
          style={{ backgroundColor: "#F7F1DE", borderLeftColor: "#C8A951" }}
        >
          <p className="text-sm text-amber-800 font-medium">
            Disclaimer: Historical performance does not guarantee future results.
            This analysis is based on backtested data and should be used for
            educational purposes only. Past regime classifications may not
            perfectly reflect real-time conditions.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 py-8 space-y-8">
        {/* Regime Distribution Chart */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h2 className="text-base font-bold text-slate-800 mb-4">
            Regime Distribution (Occurrences)
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={regimeDist}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 10 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="occurrences" radius={[4, 4, 0, 0]}>
                {regimeDist.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Forward Returns Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 overflow-x-auto">
          <h2 className="text-base font-bold text-slate-800 mb-4">
            Forward Returns by Regime
          </h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Regime</TableHead>
                <TableHead className="text-right">1M</TableHead>
                <TableHead className="text-right">3M</TableHead>
                <TableHead className="text-right">6M</TableHead>
                <TableHead className="text-right">12M</TableHead>
                <TableHead className="text-right">Occurrences</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {forwardReturns.map((r) => (
                <TableRow key={r.regime}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: r.color }}
                      />
                      <span className="text-sm font-medium">{r.regime}</span>
                    </div>
                  </TableCell>
                  <TableCell
                    className={`text-right text-sm font-medium ${
                      r.m1 > 0 ? "text-emerald-600" : "text-red-600"
                    }`}
                  >
                    {r.m1 > 0 ? "+" : ""}
                    {r.m1}%
                  </TableCell>
                  <TableCell
                    className={`text-right text-sm font-medium ${
                      r.m3 > 0 ? "text-emerald-600" : "text-red-600"
                    }`}
                  >
                    {r.m3 > 0 ? "+" : ""}
                    {r.m3}%
                  </TableCell>
                  <TableCell
                    className={`text-right text-sm font-medium ${
                      r.m6 > 0 ? "text-emerald-600" : "text-red-600"
                    }`}
                  >
                    {r.m6 > 0 ? "+" : ""}
                    {r.m6}%
                  </TableCell>
                  <TableCell
                    className={`text-right text-sm font-medium ${
                      r.m12 > 0 ? "text-emerald-600" : "text-red-600"
                    }`}
                  >
                    {r.m12 > 0 ? "+" : ""}
                    {r.m12}%
                  </TableCell>
                  <TableCell className="text-right text-sm text-slate-500">
                    {r.occurrences}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Regime Transitions */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 overflow-x-auto">
          <h2 className="text-base font-bold text-slate-800 mb-4">
            Regime Transitions
          </h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>From</TableHead>
                <TableHead>To</TableHead>
                <TableHead className="text-right">Count</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {REGIME_TRANSITIONS.map((t, i) => (
                <TableRow key={i}>
                  <TableCell className="text-sm">{t.from}</TableCell>
                  <TableCell className="text-sm">{t.to}</TableCell>
                  <TableCell className="text-right text-sm font-medium">
                    {t.count}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Caveats */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h2 className="text-base font-bold text-slate-800 mb-3">
            Important Caveats
          </h2>
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="c1">
              <AccordionTrigger className="text-sm hover:no-underline">
                <span className="font-medium">Look-ahead bias risk</span>
              </AccordionTrigger>
              <AccordionContent className="text-sm text-slate-600 leading-relaxed">
                Regime classifications are made with full knowledge of the
                period. Real-time classification may differ, especially at
                turning points when signals are mixed.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="c2">
              <AccordionTrigger className="text-sm hover:no-underline">
                <span className="font-medium">Small sample sizes</span>
              </AccordionTrigger>
              <AccordionContent className="text-sm text-slate-600 leading-relaxed">
                MP-1 (Capitulation) and MP-5 (Euphoria) have limited historical
                occurrences. Statistical significance is lower for these extreme
                regimes. Results should be interpreted with greater caution.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="c3">
              <AccordionTrigger className="text-sm hover:no-underline">
                <span className="font-medium">Changing market structure</span>
              </AccordionTrigger>
              <AccordionContent className="text-sm text-slate-600 leading-relaxed">
                Markets evolve. The rise of algorithmic trading, passive
                investing, and retail participation may change how regimes
                behave going forward compared to historical patterns.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="c4">
              <AccordionTrigger className="text-sm hover:no-underline">
                <span className="font-medium">Not investment advice</span>
              </AccordionTrigger>
              <AccordionContent className="text-sm text-slate-600 leading-relaxed">
                This analysis is for educational and informational purposes
                only. It should not be used as the sole basis for any investment
                decision. Always consult a qualified financial advisor.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </section>
    </div>
  );
}
