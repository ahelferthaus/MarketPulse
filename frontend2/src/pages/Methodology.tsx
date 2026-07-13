import {
  BarChart3,
  Newspaper,
  Layers,
  Activity,
  TrendingUp,
} from "lucide-react";
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
import { REGIME_DEFINITIONS } from "../lib/mockData";
import { getSources } from "../lib/api";
import { useAsync } from "../lib/useApi";

const indexCards = [
  {
    icon: <BarChart3 size={24} className="text-blue-500" />,
    title: "Classic Index",
    description:
      "Quantitative technical indicators including momentum, breadth, volatility, credit spreads, put/call ratios, safe-haven demand, and price strength. Pure market data — no opinions.",
    weight: "40%",
  },
  {
    icon: <Newspaper size={24} className="text-purple-500" />,
    title: "Narrative Index",
    description:
      "Sentiment analysis of financial news, headlines, and RSS feeds. Uses NLP to extract sentiment, topic modeling for macro themes, and trend analysis to gauge narrative momentum.",
    weight: "30%",
  },
  {
    icon: <Layers size={24} className="text-green-500" />,
    title: "Positioning Index",
    description:
      "Measures how investors are positioned via ETF flows, options activity, short interest, institutional holdings, and margin debt. Captures 'smart money' behavior.",
    weight: "30%",
  },
  {
    icon: <Activity size={24} className="text-amber-500" />,
    title: "Composite Score",
    description:
      "Weighted average of the three sub-indices. The final MarketPulse score that maps to one of five market regimes, from Panic (MP-1) to Euphoria (MP-5).",
    weight: "100%",
  },
];

const componentDetails = [
  {
    name: "Momentum",
    measures: "Trend strength relative to 125-day moving average",
    calculation: "(Price / SMA125 - 1) * 100, normalized to 0-100 scale",
    source: "Yahoo Finance",
    weight: "14.3%",
  },
  {
    name: "Breadth",
    measures: "Market participation via advancing vs declining volume",
    calculation: "Advancing volume / (Advancing + Declining volume)",
    source: "Yahoo Finance",
    weight: "14.3%",
  },
  {
    name: "Put/Call Ratio",
    measures: "Options market sentiment (inverted)",
    calculation: "1 - (Put volume / Call volume), clamped to 0-1",
    source: "CBOE",
    weight: "14.3%",
  },
  {
    name: "Credit Spreads",
    measures: "High-yield bond OAS spread vs investment grade",
    calculation: "Normalized OAS spread relative to 1-year range",
    source: "FRED",
    weight: "14.3%",
  },
  {
    name: "Volatility",
    measures: "Implied volatility level (VIX, inverted)",
    calculation: "(50 - VIX) / 50 * 100, clamped to 0-100",
    source: "Yahoo Finance",
    weight: "14.3%",
  },
  {
    name: "Safe Haven",
    measures: "Equity returns relative to safe-haven assets",
    calculation: "Relative performance vs bonds + gold + USD",
    source: "Yahoo Finance",
    weight: "14.3%",
  },
  {
    name: "Price Strength",
    measures: "New highs vs new lows ratio",
    calculation: "New highs / (New highs + New lows) * 100",
    source: "Yahoo Finance",
    weight: "14.3%",
  },
];

const faqItems = [
  {
    q: "How often is MarketPulse updated?",
    a: "The Classic index updates every 15 minutes during market hours. The Narrative index updates every hour as new articles are ingested. The Positioning index updates daily after market close.",
  },
  {
    q: "What markets does MarketPulse cover?",
    a: "Currently S&P 500, Nasdaq 100, Russell 2000, and Dow Jones Industrial Average. Each market has its own dedicated score calculated from market-specific data.",
  },
  {
    q: "How should I use the composite score?",
    a: "Use it as a contrarian indicator at extremes (MP-1 and MP-5) and as a trend confirmation in the middle ranges. Never use it as the sole basis for investment decisions.",
  },
  {
    q: "What does the confidence score mean?",
    a: "Confidence reflects data quality and completeness. High confidence means all data sources are active and recent. Low confidence may indicate missing data or stale feeds.",
  },
  {
    q: "Is this investment advice?",
    a: "No. MarketPulse is for educational and informational purposes only. Always consult a qualified financial advisor before making investment decisions.",
  },
  {
    q: "Can I embed MarketPulse on my website?",
    a: "Yes! Visit the Embed page to get HTML iframe, JavaScript, or JSON API code for your website or application.",
  },
];

export default function Methodology() {
  const sources = useAsync(() => getSources(), [], []);
  return (
    <div className="fade-in">
      {/* Hero */}
      <section
        className="py-12 md:py-16 px-4 md:px-8"
        style={{ backgroundColor: "#0B2240" }}
      >
        <div className="max-w-7xl mx-auto text-center">
          <BarChart3 size={40} className="mx-auto mb-4 text-blue-400" />
          <h1 className="font-display text-3xl md:text-4xl font-semibold text-white mb-3">
            How MarketPulse Works
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-sm md:text-base">
            MarketPulse combines quantitative technical analysis, narrative
            sentiment intelligence, and positioning data into a single composite
            score that identifies market regimes.
          </p>
        </div>
      </section>

      {/* Four Index Cards */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {indexCards.map((card) => (
            <div
              key={card.title}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-3">
                <div className="shrink-0 mt-0.5">{card.icon}</div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-slate-800 text-sm">
                      {card.title}
                    </h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 font-medium">
                      {card.weight}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    {card.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Five-Zone Framework */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-10">
        <h2 className="text-lg font-bold text-slate-800 mb-4">
          Five-Zone Framework
        </h2>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          {REGIME_DEFINITIONS.map((regime) => (
            <div key={regime.zone} className="flex items-center gap-4">
              <div
                className="w-4 h-12 rounded shrink-0"
                style={{ backgroundColor: regime.color }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-slate-800">
                    {regime.zone} — {regime.label}
                  </span>
                  <span className="text-xs text-slate-400">{regime.range}</span>
                </div>
                <p className="text-sm text-slate-500 mt-0.5">
                  {regime.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Component Details */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-10">
        <h2 className="text-lg font-bold text-slate-800 mb-4">
          Component Details
        </h2>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <Accordion type="single" collapsible className="w-full">
            {componentDetails.map((c, i) => (
              <AccordionItem key={c.name} value={`item-${i}`}>
                <AccordionTrigger className="px-5 py-3 text-sm hover:no-underline">
                  <div className="flex items-center gap-3">
                    <TrendingUp size={16} className="text-blue-500" />
                    <span className="font-semibold">{c.name}</span>
                    <span className="text-xs text-slate-400 font-normal">
                      {c.weight}
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-5 pb-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-slate-400 text-xs uppercase tracking-wider">
                        Measures
                      </span>
                      <p className="text-slate-700 mt-0.5">{c.measures}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-xs uppercase tracking-wider">
                        Calculation
                      </span>
                      <p className="text-slate-700 mt-0.5">{c.calculation}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-xs uppercase tracking-wider">
                        Source
                      </span>
                      <p className="text-slate-700 mt-0.5">{c.source}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-xs uppercase tracking-wider">
                        Weight in Classic
                      </span>
                      <p className="text-slate-700 mt-0.5">{c.weight}</p>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* Data Sources */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-10">
        <h2 className="text-lg font-bold text-slate-800 mb-4">Data Sources</h2>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Provider</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Data Type</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sources.map((s) => (
                <TableRow key={s.provider}>
                  <TableCell className="font-medium text-sm">
                    {s.provider}
                  </TableCell>
                  <TableCell>
                    <span
                      className="text-xs px-2 py-0.5 rounded-full font-medium capitalize"
                      style={{
                        backgroundColor:
                          s.tier === "public"
                            ? "#6F9A3D18"
                            : s.tier === "premium"
                              ? "#3B82D618"
                              : "#6E3F8718",
                        color:
                          s.tier === "public"
                            ? "#6F9A3D"
                            : s.tier === "premium"
                              ? "#3B82D6"
                              : "#6E3F87",
                      }}
                    >
                      {s.tier}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor: s.available ? "#6F9A3D" : "#B3382E",
                        }}
                      />
                      <span className="text-sm">
                        {s.available ? "Active" : "Unavailable"}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-slate-500">
                    {s.dataFreshness}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-12">
        <h2 className="text-lg font-bold text-slate-800 mb-4">
          Frequently Asked Questions
        </h2>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <Accordion type="single" collapsible className="w-full">
            {faqItems.map((item, i) => (
              <AccordionItem key={i} value={`faq-${i}`}>
                <AccordionTrigger className="px-5 py-3 text-sm hover:no-underline">
                  <span className="font-medium text-left">{item.q}</span>
                </AccordionTrigger>
                <AccordionContent className="px-5 pb-4 text-sm text-slate-600 leading-relaxed">
                  {item.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>
    </div>
  );
}
