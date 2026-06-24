import { Link } from "react-router";
import {
  Activity,
  BookOpen,
  MessageSquare,
  Layers,
} from "lucide-react";
import PulseGauge from "../components/PulseGauge";
import PulseCard from "../components/PulseCard";
import StackedPulseChart from "../components/StackedPulseChart";
import ComponentBreakdown from "../components/ComponentBreakdown";
import ExplanationBox from "../components/ExplanationBox";
import {
  MOCK_COMPOSITE_SCORE,
  MOCK_REGIME,
  MOCK_REGIME_LABEL,
  MOCK_SUB_INDICES,
  MOCK_CONFIDENCE,
  MOCK_EXPLANATION,
  MOCK_WHAT_CHANGED,
  MOCK_WHY_IT_MATTERS,
  MOCK_HISTORY,
} from "../lib/mockData";

export default function Home() {
  const latest = MOCK_HISTORY[MOCK_HISTORY.length - 1];
  const prevDay = MOCK_HISTORY[MOCK_HISTORY.length - 2];
  const prevWeek = MOCK_HISTORY[MOCK_HISTORY.length - 8];

  const change1d = latest
    ? Math.round((latest.composite - (prevDay?.composite ?? latest.composite)) * 10) / 10
    : 0;
  const change1w = latest
    ? Math.round((latest.composite - (prevWeek?.composite ?? latest.composite)) * 10) / 10
    : 0;

  // Last 30 days of history for sparklines
  const last30 = MOCK_HISTORY.slice(-30);
  const classicHistory = last30.map((h) => h.classic);
  const narrativeHistory = last30.map((h) => h.narrative);
  const positioningHistory = last30.map((h) => h.positioning);

  return (
    <div className="fade-in">
      {/* Hero */}
      <section
        className="py-12 md:py-16 px-4 md:px-8"
        style={{ backgroundColor: "#0A1628" }}
      >
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center">
          <div className="flex items-center gap-2 mb-6">
            <Activity size={16} className="text-emerald-400" />
            <span className="text-emerald-400 text-sm font-medium">
              Live &middot; Updated 2 min ago
            </span>
          </div>

          <PulseGauge
            score={MOCK_COMPOSITE_SCORE}
            regime={MOCK_REGIME}
            label={MOCK_REGIME_LABEL}
            change1d={change1d}
            change1w={change1w}
          />

          <p className="mt-6 text-slate-300 text-sm max-w-xl leading-relaxed">
            {MOCK_EXPLANATION}
          </p>
          <p className="mt-2 text-slate-500 text-xs">
            Last updated: January 15, 2026 at 4:30 PM ET
          </p>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 w-full max-w-2xl">
            {[
              { label: "Confidence", value: `${MOCK_CONFIDENCE}%` },
              { label: "Direction", value: "Rising", color: "#22C55E" },
              { label: "S&P 500", value: `4,${(Math.round(latest?.sp500 ?? 0)).toLocaleString()}` },
              { label: "Data Sources", value: "4/6 Active" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-lg p-3 text-center"
                style={{ backgroundColor: "rgba(255,255,255,0.05)" }}
              >
                <div
                  className="text-lg font-bold"
                  style={{ color: stat.color ?? "#F8FAFC" }}
                >
                  {stat.value}
                </div>
                <div className="text-xs text-slate-400 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sub-Index Cards */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <PulseCard
            name="Classic"
            score={MOCK_SUB_INDICES.classic.score}
            change1d={MOCK_SUB_INDICES.classic.change1d}
            change1w={MOCK_SUB_INDICES.classic.change1w}
            regime={MOCK_SUB_INDICES.classic.label}
            confidence={MOCK_SUB_INDICES.classic.confidence}
            history={classicHistory}
          />
          <PulseCard
            name="Narrative"
            score={MOCK_SUB_INDICES.narrative.score}
            change1d={MOCK_SUB_INDICES.narrative.change1d}
            change1w={MOCK_SUB_INDICES.narrative.change1w}
            regime={MOCK_SUB_INDICES.narrative.label}
            confidence={MOCK_SUB_INDICES.narrative.confidence}
            history={narrativeHistory}
          />
          <PulseCard
            name="Positioning"
            score={MOCK_SUB_INDICES.positioning.score}
            change1d={MOCK_SUB_INDICES.positioning.change1d}
            change1w={MOCK_SUB_INDICES.positioning.change1w}
            regime={MOCK_SUB_INDICES.positioning.label}
            confidence={MOCK_SUB_INDICES.positioning.confidence}
            history={positioningHistory}
          />
        </div>
      </section>

      {/* Stacked Chart */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-8">
        <StackedPulseChart />
      </section>

      {/* Explanation Boxes */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ExplanationBox
            icon={<MessageSquare size={18} />}
            title="What Changed"
            text={MOCK_WHAT_CHANGED}
            timestamp="Jan 15, 2026 4:30 PM ET"
          />
          <ExplanationBox
            icon={<BookOpen size={18} />}
            title="Why It Matters"
            text={MOCK_WHY_IT_MATTERS}
          />
        </div>
      </section>

      {/* Component Breakdown */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-8">
        <ComponentBreakdown />
      </section>

      {/* Bottom CTA */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-12">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center">
          <Layers size={32} className="mx-auto mb-4 text-slate-400" />
          <h3 className="text-lg font-bold text-slate-800 mb-2">
            Understand the Methodology
          </h3>
          <p className="text-sm text-slate-500 mb-4 max-w-md mx-auto">
            Dive deeper into how MarketPulse scores are calculated, what data
            sources we use, and how to interpret the signals.
          </p>
          <Link
            to="/methodology"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-white transition-colors hover:opacity-90"
            style={{ backgroundColor: "#0A1628" }}
          >
            <BookOpen size={16} />
            Explore our methodology
          </Link>
        </div>
      </section>
    </div>
  );
}
