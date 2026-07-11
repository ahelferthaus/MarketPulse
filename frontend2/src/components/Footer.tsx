import { Link } from "react-router";
import { DATA_MODE } from "../lib/api";

export default function Footer() {
  return (
    <footer style={{ backgroundColor: "#081A33" }}>
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-10">
        <div className="flex flex-col md:flex-row md:items-start gap-8">
          <div className="max-w-sm">
            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-[10px] font-bold tracking-[0.28em] uppercase" style={{ color: "#C8A951" }}>
                Westwood
              </span>
              <span className="font-display text-white text-base">MarketPulse</span>
            </div>
            <p className="text-[13px] leading-relaxed" style={{ color: "rgba(255,255,255,0.55)" }}>
              Four daily 0–100 readings of market psychology — classic
              indicators, the news narrative, and investor positioning,
              blended into one composite barometer.
            </p>
          </div>

          <div className="md:ml-auto flex gap-12">
            <div>
              <h4 className="text-[11px] font-semibold uppercase tracking-[0.16em] mb-3" style={{ color: "rgba(255,255,255,0.45)" }}>
                Go deeper
              </h4>
              <ul className="space-y-1.5 text-[13px]">
                {[
                  { to: "/methodology", label: "Methodology" },
                  { to: "/markets", label: "Markets" },
                  { to: "/backtest", label: "Backtest" },
                  { to: "/embed-demo", label: "Embed the widget" },
                ].map((l) => (
                  <li key={l.to}>
                    <Link to={l.to} className="transition-colors hover:text-white" style={{ color: "rgba(255,255,255,0.6)" }}>
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="max-w-xs">
              <h4 className="text-[11px] font-semibold uppercase tracking-[0.16em] mb-3" style={{ color: "rgba(255,255,255,0.45)" }}>
                The fine print
              </h4>
              <p className="text-[12px] leading-relaxed" style={{ color: "rgba(255,255,255,0.5)" }}>
                MarketPulse is an educational market-sentiment tool, not
                investment advice and not a trading signal. Data may be
                delayed or derived from public and proxy sources.
              </p>
            </div>
          </div>
        </div>

        <div
          className="mt-8 pt-5 flex flex-col sm:flex-row items-center gap-2 text-[11px]"
          style={{ borderTop: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.4)" }}
        >
          <span>© 2026 Westwood Holdings Group. All rights reserved.</span>
          <span className="sm:ml-auto font-data">
            data mode: {DATA_MODE === "live" ? "live API" : "static snapshot"}
          </span>
        </div>
      </div>
    </footer>
  );
}
