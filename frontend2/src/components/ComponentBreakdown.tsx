import { useState } from "react";
import { ArrowUpDown } from "lucide-react";
import { MOCK_COMPONENTS, type ComponentData } from "../lib/mockData";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type SortKey = "name" | "score" | "weight" | "contribution" | "direction";
type SortDir = "asc" | "desc";

const directionColor: Record<string, string> = {
  bullish: "#22C55E",
  bearish: "#DC2626",
  neutral: "#6B7280",
};

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

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 fade-in overflow-x-auto">
      <h3 className="font-bold text-slate-800 text-base mb-4">
        Component Breakdown
      </h3>
      <Table>
        <TableHeader>
          <TableRow>
            {(["name", "score", "weight", "contribution", "direction"] as SortKey[]).map(
              (key) => (
                <TableHead
                  key={key}
                  className="cursor-pointer select-none"
                  onClick={() => toggleSort(key)}
                >
                  <div className="flex items-center gap-1">
                    <span className="capitalize">{key}</span>
                    <ArrowUpDown size={12} className="text-slate-400" />
                  </div>
                </TableHead>
              )
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((c: ComponentData) => (
            <TableRow key={c.name}>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{
                      backgroundColor: directionColor[c.direction],
                    }}
                  />
                  <div>
                    <div className="text-sm font-medium">{c.name}</div>
                    <div className="text-xs text-slate-400">{c.description}</div>
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${c.score}%`,
                        backgroundColor: directionColor[c.direction],
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium">{c.score}</span>
                </div>
              </TableCell>
              <TableCell className="text-sm">
                {(c.weight * 100).toFixed(1)}%
              </TableCell>
              <TableCell className="text-sm font-medium">
                {c.contribution.toFixed(1)}%
              </TableCell>
              <TableCell>
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize"
                  style={{
                    backgroundColor: directionColor[c.direction] + "18",
                    color: directionColor[c.direction],
                  }}
                >
                  {c.direction}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
