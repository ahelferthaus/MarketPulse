import { Link } from "react-router";
import { MessageSquare, BookOpen, ArrowRight } from "lucide-react";
import PulseGauge from "../components/PulseGauge";
import PulseCard from "../components/PulseCard";
import StackedPulseChart from "../components/StackedPulseChart";
import ComponentBreakdown from "../components/ComponentBreakdown";
import ExplanationBox from "../components/ExplanationBox";
import { getDashboard, getComponents, getSources, mockDashboard, freshness, DATA_MODE } from "../lib/api";
import { useAsync } from "../lib/useApi";
import { ZONES, zoneFor, headline, BRAND } from "../lib/theme";

const SUB_BLURBS: Record<string, string> = {
  Classic: "Prices, volatility, breadth, credit — what the market is doing.",
  Narrative: "News and financial text — what the market is saying.",
  Positioning: "Options, term structure, safe havens — where money is leaning.",
};

export default function Home() {
  const dash = useAsync(() => getDashboard("sp500"), mockDashboard(), []);
  const components = useAsync(() => getComponents("sp500"), [], []);
  const sources = useAsync(() => getSources(), [], []);

  const change1d = Math.round(dash.change1d * 10) / 10;
  const change1w = Math.round(dash.change1w * 10) / 10;
  const zone = zoneFor(dash.composite);

  const last30 = dash.history.slice(-30);
  const activeSources = sources.filter((s) => s.available).length;

  return (
    <div className="fade-in">
      {/* ── Hero: the barometer ─────────────────────────────────── */}
      <section
        className="px-4 md:px-8"
        style={{
          background: `radial-gradient(1100px 520px at 30% 0%, ${BRAND.navy800}66, transparent 62%), linear-gradient(170deg, ${BRAND.navy900} 0%, ${BRAND.navy950} 78%)`,
        }}
      >
        <div className="max-w-7xl mx-auto py-10 md:py-14 grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-10 items-center">
          {/* dial */}
          <div className="order-2 lg:order-1">
            <PulseGauge
              score={dash.composite}
              regime={dash.regime}
              label={dash.regimeLabel}
              change1d={change1d}
              change1w={change1w}
            />
          </div>

          {/* today's read */}
          <div className="order-1 lg:order-2">
            <div className="text-[11px] font-semibold uppercase" style={{ color: BRAND.gold, letterSpacing: "0.22em" }}>
              Market barometer · S&amp;P 500
            </div>
            <h1
              className="font-display text-white mt-3 leading-tight"
              style={{ fontSize: "clamp(28px, 3.4vw, 42px)", fontWeight: 600 }}
            >
              {headline(zone.id, dash.direction)}
            </h1>
            <p className="mt-4 text-[15px] leading-relaxed" style={{ color: "rgba(255,255,255,0.72)" }}>
              {dash.explanation}
            </p>

            {/* confidence */}
            <div className="mt-6 max-w-sm">
              <div className="flex items-baseline justify-between text-[11px] mb-1.5">
                <span className="uppercase tracking-[0.14em]" style={{ color: "rgba(255,255,255,0.5)" }}>
                  Data confidence
                </span>
                <span className="font-data" style={{ color: "rgba(255,255,255,0.75)" }}>
                  {dash.confidence}%{sources.length > 0 && ` · ${activeSources} of ${sources.length} sources reporting`}
                </span>
              </div>
              <div className="h-[5px] rounded-full" style={{ backgroundColor: "rgba(255,255,255,0.12)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${dash.confidence}%`,
                    background: `linear-gradient(90deg, ${BRAND.goldDeep}, ${BRAND.gold})`,
                    transition: "width 1s ease-out",
                  }}
                />
              </div>
            </div>

            {/* as-of — honest, from the payload */}
            <p className="font-data text-[11px] mt-6" style={{ color: "rgba(255,255,255,0.42)" }}>
              As of {freshness(dash.asOf)} · {DATA_MODE === "live" ? "live API" : "static snapshot, refreshed daily"}
            </p>
          </div>
        </div>

        {/* zone strip — the framework, with today highlighted */}
        <div className="max-w-7xl mx-auto pb-10">
          <div className="grid grid-cols-5 gap-[3px] rounded-lg overflow-hidden" role="list" aria-label="The five MarketPulse zones">
            {ZONES.map((z) => {
              const active = z.id === zone.id;
              return (
                <div
                  key={z.id}
                  role="listitem"
                  className="px-2 py-2.5 text-center transition-all"
                  style={{
                    backgroundColor: active ? z.onNavy : "rgba(255,255,255,0.05)",
                    boxShadow: active ? "inset 0 0 0 1px rgba(255,255,255,0.35)" : "none",
                  }}
                >
                  <div
                    className="font-data text-[10px]"
                    style={{ color: active ? "rgba(255,255,255,0.85)" : "rgba(255,255,255,0.4)" }}
                  >
                    {z.zone} · {z.min}–{z.max}
                  </div>
                  <div
                    className="text-[12px] font-semibold mt-0.5"
                    style={{ color: active ? "#fff" : "rgba(255,255,255,0.55)" }}
                  >
                    {z.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Three lenses ────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pt-10">
        <div className="mp-eyebrow mb-3">Three lenses, one composite</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(["classic", "narrative", "positioning"] as const).map((key) => {
            const s = dash.subIndices[key];
            const name = key.charAt(0).toUpperCase() + key.slice(1);
            return (
              <PulseCard
                key={key}
                name={name}
                score={s.score}
                change1d={s.change1d}
                change1w={s.change1w}
                regime={s.label}
                confidence={s.confidence}
                history={last30.map((h) => h[key])}
                blurb={SUB_BLURBS[name]}
              />
            );
          })}
        </div>
      </section>

      {/* ── History ─────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pt-8">
        <StackedPulseChart data={dash.history} />
      </section>

      {/* ── What changed (only when the backend actually says) ──── */}
      {dash.whatChanged && (
        <section className="max-w-7xl mx-auto px-4 md:px-8 pt-8">
          <ExplanationBox
            icon={<MessageSquare size={17} />}
            title="What changed"
            text={dash.whatChanged}
            timestamp={dash.asOf ? `As of ${freshness(dash.asOf)}` : undefined}
          />
        </section>
      )}

      {/* ── Components ──────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 pt-8">
        <ComponentBreakdown components={components} />
      </section>

      {/* ── Methodology link — quiet ────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-10">
        <Link
          to="/methodology"
          className="mp-panel flex items-center gap-4 p-5 transition-shadow hover:shadow-md group"
        >
          <BookOpen size={20} style={{ color: BRAND.goldDeep }} />
          <div>
            <div className="text-[14px] font-semibold" style={{ color: BRAND.ink }}>
              How the barometer is built
            </div>
            <div className="text-[12.5px]" style={{ color: BRAND.slate }}>
              Nine components, three lenses, five zones — the full methodology, openly documented.
            </div>
          </div>
          <ArrowRight size={18} className="ml-auto transition-transform group-hover:translate-x-1" style={{ color: BRAND.slateFaint }} />
        </Link>
      </section>
    </div>
  );
}
