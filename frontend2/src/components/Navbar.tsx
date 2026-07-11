import { useState } from "react";
import { Link, useLocation } from "react-router";
import { Menu, X } from "lucide-react";

const navLinks = [
  { to: "/", label: "Barometer" },
  { to: "/markets", label: "Markets" },
  { to: "/backtest", label: "Backtest" },
  { to: "/methodology", label: "Methodology" },
  { to: "/admin", label: "Data desk" },
];

export default function Navbar() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 h-16"
      style={{
        backgroundColor: "rgba(8,26,51,0.96)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(200,169,81,0.35)",
      }}
    >
      <div className="max-w-7xl mx-auto h-full flex items-center justify-between px-4 md:px-8">
        {/* Masthead */}
        <Link to="/" className="flex items-baseline gap-2.5 shrink-0">
          <span
            className="text-[10px] font-bold tracking-[0.28em] uppercase"
            style={{ color: "#C8A951" }}
          >
            Westwood
          </span>
          <span className="font-display text-white text-lg leading-none">
            MarketPulse
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-0.5">
          {navLinks.map((link) => {
            const active = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                className="relative px-3.5 py-2 text-[13px] font-medium transition-colors"
                style={{ color: active ? "#FFFFFF" : "rgba(255,255,255,0.62)" }}
              >
                {link.label}
                {active && (
                  <span
                    aria-hidden
                    className="absolute left-3.5 right-3.5 -bottom-[1px] h-[2px]"
                    style={{ backgroundColor: "#C8A951" }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-lg transition-colors"
          style={{ color: "rgba(255,255,255,0.7)" }}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div
          className="absolute top-16 left-0 right-0 md:hidden p-4 flex flex-col gap-1"
          style={{ backgroundColor: "rgba(8,26,51,0.98)" }}
        >
          {navLinks.map((link) => {
            const active = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className="px-4 py-3 text-sm font-medium rounded-lg"
                style={{
                  color: active ? "#fff" : "rgba(255,255,255,0.65)",
                  borderLeft: active ? "2px solid #C8A951" : "2px solid transparent",
                }}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      )}
    </nav>
  );
}
