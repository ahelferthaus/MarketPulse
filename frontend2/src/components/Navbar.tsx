import { useState } from "react";
import { Link, useLocation } from "react-router";
import { Sun, Moon, Menu, X } from "lucide-react";

const navLinks = [
  { to: "/", label: "Dashboard" },
  { to: "/methodology", label: "Methodology" },
  { to: "/markets", label: "Markets" },
  { to: "/backtest", label: "Backtest" },
  { to: "/admin", label: "Admin" },
];

export default function Navbar() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dark, setDark] = useState(false);

  const toggleTheme = () => setDark(!dark);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 h-16 flex items-center justify-between px-4 md:px-8"
      style={{ backgroundColor: "rgba(10,22,40,0.95)", backdropFilter: "blur(12px)" }}
    >
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2 shrink-0">
        <span
          className="text-xs font-bold tracking-[0.2em] uppercase"
          style={{ color: "#D4AF37" }}
        >
          WESTWOOD
        </span>
        <span className="text-white font-semibold text-sm md:text-base">
          MarketPulse
        </span>
      </Link>

      {/* Desktop Nav */}
      <div className="hidden md:flex items-center gap-1">
        {navLinks.map((link) => {
          const active = location.pathname === link.to;
          return (
            <Link
              key={link.to}
              to={link.to}
              className={`px-4 py-2 text-sm font-medium transition-colors rounded-md ${
                active
                  ? "text-white border-b-2 border-white"
                  : "text-slate-300 hover:text-white hover:bg-white/10"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>

      {/* Right */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 text-slate-300 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          aria-label="Toggle theme"
        >
          {dark ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 text-slate-300 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div
          className="absolute top-16 left-0 right-0 md:hidden p-4 flex flex-col gap-1"
          style={{ backgroundColor: "rgba(10,22,40,0.98)" }}
        >
          {navLinks.map((link) => {
            const active = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className={`px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  active
                    ? "text-white bg-white/10 border-l-2 border-white"
                    : "text-slate-300 hover:text-white hover:bg-white/5"
                }`}
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
