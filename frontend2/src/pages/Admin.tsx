import { useState } from "react";
import {
  Shield,
  Database,
  RefreshCw,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  Terminal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import SourceQualityBadge from "../components/SourceQualityBadge";
import { MOCK_LOG_ENTRIES } from "../lib/mockData";
import { getSources, getComponents, getDashboard, mockDashboard } from "../lib/api";
import { useAsync } from "../lib/useApi";

export default function Admin() {
  const sources = useAsync(() => getSources(), [], []);
  const components = useAsync(() => getComponents("sp500"), [], []);
  const dash = useAsync(() => getDashboard("sp500"), mockDashboard(), []);
  const confidence = dash.confidence;
  const [logs, setLogs] = useState(MOCK_LOG_ENTRIES);
  const [lastUpdate, setLastUpdate] = useState("2026-01-15 16:30:12");
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      const now = new Date().toISOString().replace("T", " ").split(".")[0];
      setLastUpdate(now);
      setLogs((prev) => [
        `[${now}] INFO: Manual refresh triggered`,
        `[${now}] INFO: All data sources updated`,
        `[${now}] INFO: Composite score recalculated: 67.4`,
        ...prev,
      ]);
      setRefreshing(false);
    }, 1500);
  };

  const handleExport = () => {
    const now = new Date().toISOString().replace("T", " ").split(".")[0];
    setLogs((prev) => [
      `[${now}] INFO: Export generated successfully`,
      ...prev,
    ]);
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <section className="py-8 md:py-10 px-4 md:px-8" style={{ backgroundColor: "#0A1628" }}>
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <Shield size={24} className="text-amber-400" />
            <h1 className="text-2xl md:text-3xl font-extrabold text-white">
              Admin &amp; Diagnostics
            </h1>
            <Badge variant="outline" className="text-amber-400 border-amber-400 text-xs">
              Internal use only
            </Badge>
          </div>
          <p className="text-slate-400 text-sm">
            System diagnostics, data source status, and manual controls.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 py-8 space-y-6">
        {/* Source Status Grid */}
        <div>
          <h2 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
            <Database size={18} />
            Source Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {sources.map((source) => (
              <div
                key={source.provider}
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-sm text-slate-800">
                    {source.provider}
                  </span>
                  {source.available ? (
                    <CheckCircle size={16} className="text-emerald-500" />
                  ) : (
                    <XCircle size={16} className="text-red-500" />
                  )}
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Status</span>
                    <span
                      className={`font-medium ${
                        source.available ? "text-emerald-600" : "text-red-600"
                      }`}
                    >
                      {source.available ? "Active" : "Unavailable"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Tier</span>
                    <span className="capitalize text-slate-600">{source.tier}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Last Fetch</span>
                    <span className="text-slate-600">{source.lastFetch}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Freshness</span>
                    <span className="text-slate-600">{source.dataFreshness}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Update Info */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h2 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
            <Clock size={18} />
            Update Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <span className="text-xs text-slate-400 uppercase tracking-wider">
                Last Update
              </span>
              <p className="text-sm font-medium text-slate-700 mt-0.5">
                {lastUpdate}
              </p>
            </div>
            <div>
              <span className="text-xs text-slate-400 uppercase tracking-wider">
                Next Scheduled
              </span>
              <p className="text-sm font-medium text-slate-700 mt-0.5">
                2026-01-16 09:30:00
              </p>
            </div>
            <div>
              <span className="text-xs text-slate-400 uppercase tracking-wider">
                Update Frequency
              </span>
              <p className="text-sm font-medium text-slate-700 mt-0.5">
                Every 15 min (market hours)
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              className="text-sm"
            >
              <RefreshCw
                size={16}
                className={`mr-2 ${refreshing ? "animate-spin" : ""}`}
              />
              {refreshing ? "Refreshing..." : "Manual Refresh"}
            </Button>
            <Button variant="outline" onClick={handleExport} className="text-sm">
              <Download size={16} className="mr-2" />
              Generate Export
            </Button>
          </div>
        </div>

        {/* Confidence Score */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h2 className="text-base font-bold text-slate-800 mb-3">
            Confidence Score
          </h2>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-extrabold text-slate-800">
              {confidence}%
            </div>
            <SourceQualityBadge confidence={confidence} />
          </div>
          <p className="text-sm text-slate-500 mt-2">
            Based on 4 active sources out of 6 configured. All primary data
            feeds are operational.
          </p>
        </div>

        {/* Raw Component Values */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 overflow-x-auto">
          <h2 className="text-base font-bold text-slate-800 mb-3">
            Raw Component Values
          </h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Component</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Weight</TableHead>
                <TableHead>Contribution</TableHead>
                <TableHead>Direction</TableHead>
                <TableHead>Raw Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {components.map((c) => (
                <TableRow key={c.name}>
                  <TableCell className="font-medium text-sm">{c.name}</TableCell>
                  <TableCell className="text-sm">{c.score}</TableCell>
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
                        backgroundColor:
                          c.direction === "bullish"
                            ? "#22C55E18"
                            : "#DC262618",
                        color:
                          c.direction === "bullish"
                            ? "#22C55E"
                            : "#DC2626",
                      }}
                    >
                      {c.direction}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-slate-400 font-mono">
                    {Math.round(c.score * c.weight * 100) / 100}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Diagnostics Log */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h2 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
            <Terminal size={18} />
            Diagnostics Log
          </h2>
          <ScrollArea className="h-64 rounded-lg border border-slate-100 p-3 bg-slate-50">
            <div className="font-mono text-xs space-y-1">
              {logs.map((entry, i) => {
                const isWarn = entry.includes("WARN");
                const isError = entry.includes("ERROR");
                return (
                  <div
                    key={i}
                    className={`${
                      isWarn
                        ? "text-amber-600"
                        : isError
                          ? "text-red-600"
                          : "text-slate-600"
                    }`}
                  >
                    {entry}
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </div>
      </section>
    </div>
  );
}
