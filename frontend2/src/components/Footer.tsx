import { Link } from "react-router";
import { TrendingUp } from "lucide-react";

export default function Footer() {
  return (
    <footer style={{ backgroundColor: "#0A1728" }} className="text-slate-400">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp size={20} style={{ color: "#D4AF37" }} />
              <span className="text-white font-semibold">Westwood MarketPulse</span>
            </div>
            <p className="text-sm leading-relaxed">
              Market sentiment and risk appetite analysis powered by quantitative
              indicators, narrative intelligence, and positioning data.
            </p>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">
              Resources
            </h4>
            <ul className="space-y-2">
              <li>
                <Link
                  to="/methodology"
                  className="text-sm hover:text-white transition-colors"
                >
                  Methodology
                </Link>
              </li>
              <li>
                <Link
                  to="/markets"
                  className="text-sm hover:text-white transition-colors"
                >
                  Markets
                </Link>
              </li>
              <li>
                <Link
                  to="/embed-demo"
                  className="text-sm hover:text-white transition-colors"
                >
                  Embed Widget
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">
              Legal
            </h4>
            <p className="text-sm leading-relaxed">
              <strong className="text-slate-300">Disclaimer:</strong> For
              educational purposes only. Not investment advice. Past performance
              does not guarantee future results.
            </p>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-10 pt-6 border-t border-slate-700/50 text-center text-xs">
          &copy; 2026 Westwood. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
