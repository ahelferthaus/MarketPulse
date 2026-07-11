/**
 * Component breakdown — nine inputs, one diverging read.
 *
 * Each component's 0-100 score is drawn as a thin diverging bar around the
 * neutral 50 line: bearish reads pull left in red, bullish reads push right
 * in green. Direction is never color-alone — the chip carries the word.
 */
import { useState } from "react";
import { ArrowUpDown } from "lucide-react";
import { MOCK_COMPONENTS, type ComponentData } from "../lib/mockData";
import { BRAND } from "../lib/theme";

type SortKey = "name" | "score" | "weight" | "contribution";
type SortDir = "asc" | "desc";

const DIR = {
  bullish: { color: "#4E7325", bg: "#6F9A3D", label: "Bullish" },
  bearish: { color: "#A33328", bg: "#B3382E", label: "Bearish" },
  neutral: { color: BRAND.slate, bg: "#8B93A1", label: "Neutral" },
} as const;

function DivergingBar({ score }: { score: number }) {
  // bar spans from 50 to the score; the 50 line is always visible
  const from = Math.min(50, score);
  const to = Math.max(50, score);
  const color = score >= 56 ? DIR.bullish.bg : score <= 44 ? DIR.bearish.bg : DIR.neutral.bg;
  return (
    <div className="relative w-32 h-[7px] rounded-full" style={{ backgroundColor: "#EEF1F5" }}>
      <div
        className="absolute top-0 h-full rounded-full"
        style={{ left: `${from}%`, width: `${Math.max(to - from, 1.5)}%`, backgroundColor: color }}
      />
      <div
        className="absolute top-[-3px] h-[13px] w-px"
        style={{ left: "50%", backgroundColor: BRAND.slateFaint }}
        aria-hidden
      />
    </div>
  );
}

interface ComponentBreakdownProps {
  components?: ComponentData[];
}

export default function ComponentBreakdown({
  components = MOCK_COMPONENTS,
}: ComponentBreakdownProps) {
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({
    key: "contribution",
    dir: "desc",
  });

  const sorted = [...components].sort((a, b) => {
    const va = a[sort.key];
    const vb = b[sort.key];
    if (typeof va === "string" && typeof vb === "string") {
      return sort.dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    return sort.dir === "asc"
      ? (va as number) - (vb as number)
      : (vb as number) - (va as number);
  });

  function toggleSort(key: SortKey) {
    setSort((prev) => ({
      key,
      dir: prev.key === key && prev.dir === "desc" ? "asc" : "desc",
    }));
  }

  const TH = ({ k, children, className = "" }: { k: SortKey; children: React.ReactNode; className?: string }) => (
    <th
      className={`text-left text-[11px] font-semibold uppercase tracking-wider py-2 cursor-pointer select-none ${className}`}
      style={{ color: BRAND.slateFaint }}
      onClick={() => toggleSort(k)}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        <ArrowUpDown size={11} aria-hidden />
      </span>
    </th>
  );

  return (
    <div className="mp-panel p-5 md:p-6 fade-in overflow-x-auto">
      <div className="mp-eyebrow">Under the hood</div>
      <h3 className="font-display text-lg mt-0.5 mb-4" style={{ color: BRAND.ink }}>
        What is moving the score
      </h3>
      <table className="w-full min-w-[640px]">
        <thead>
          <tr className="border-b" style={{ borderColor: BRAND.hairline }}>
            <TH k="name">Component</TH>
            <TH k="score">Read vs neutral</TH>
            <TH k="score" className="text-right">Score</TH>
            <TH k="weight" className="text-right">Weight</TH>
            <TH k="contribution" className="text-right">Contribution</TH>
            <th className="text-left text-[11px] font-semibold uppercase tracking-wider py-2 pl-6" style={{ color: BRAND.slateFaint }}>
              Direction
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((c: ComponentData) => {
            const d = DIR[c.direction] ?? DIR.neutral;
            return (
              <tr key={c.name} className="border-b last:border-0" style={{ borderColor: BRAND.hairline }}>
                <td className="py-2.5 pr-4">
                  <div className="text-[13px] font-medium" style={{ color: BRAND.ink }}>{c.name}</div>
                  {c.description && (
                    <div className="text-[11px]" style={{ color: BRAND.slateFaint }}>{c.description}</div>
                  )}
                </td>
                <td className="py-2.5 pr-4"><DivergingBar score={c.score} /></td>
                <td className="py-2.5 pr-4 text-right font-data text-[13px]" style={{ color: BRAND.ink }}>
                  {c.score}
                </td>
                <td className="py-2.5 pr-4 text-right font-data text-[13px]" style={{ color: BRAND.slate }}>
                  {(c.weight * 100).toFixed(1)}%
                </td>
                <td className="py-2.5 pr-4 text-right font-data text-[13px]" style={{ color: BRAND.ink }}>
                  {c.contribution.toFixed(1)}
                </td>
                <td className="py-2.5 pl-6">
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold"
                    style={{
                      color: d.color,
                      backgroundColor: `${d.bg}14`,
                      border: `1px solid ${d.bg}50`,
                    }}
                  >
                    {d.label}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="text-[11px] mt-3" style={{ color: BRAND.slateFaint }}>
        Bars diverge from the neutral 50 line. Contribution = score × weight.
      </p>
    </div>
  );
}
