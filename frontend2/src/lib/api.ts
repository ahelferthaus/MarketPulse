/**
 * MarketPulse data layer.
 *
 * Resolves data from one of two sources, with mock data as a final fallback:
 *
 *   - LIVE   — when VITE_API_BASE_URL is set, calls the FastAPI backend
 *              (e.g. https://api.example.com/api/v1/scores/current?market=sp500)
 *   - STATIC — otherwise, fetches pre-generated JSON bundled with the site
 *              (e.g. /MarketPulse/data/scores-current-sp500.json)
 *
 * The static payloads are produced by `backend/jobs/generate_frontend_payloads.py`,
 * which calls the same endpoints — so the two modes return identical shapes and
 * switching to a hosted backend later is just setting one env var.
 *
 * Every endpoint function catches its own errors and returns mock data, so the
 * UI never breaks if a payload is missing or the backend is unreachable.
 */

import {
  MOCK_HISTORY,
  MOCK_COMPONENTS,
  MOCK_SOURCES,
  MOCK_SUB_INDICES,
  MOCK_COMPOSITE_SCORE,
  MOCK_REGIME,
  MOCK_REGIME_LABEL,
  MOCK_DIRECTION,
  MOCK_CONFIDENCE,
  MOCK_EXPLANATION,
  FORWARD_RETURNS,
  MARKET_CONFIGS,
  type HistoryPoint,
  type ComponentData,
  type SourceStatusData,
} from "./mockData";

// ── Configuration ─────────────────────────────────────────────────────────

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)
  ?.replace(/\/$/, "");
const STATIC_BASE = `${import.meta.env.BASE_URL}data/`;

export const DATA_MODE: "live" | "static" = API_BASE ? "live" : "static";

async function load(
  livePath: string,
  query: Record<string, string>,
  staticKey: string,
): Promise<any> {
  let url: string;
  if (API_BASE) {
    const qs = new URLSearchParams(query).toString();
    url = `${API_BASE}/api/v1/${livePath}${qs ? `?${qs}` : ""}`;
  } else {
    url = `${STATIC_BASE}${staticKey}.json`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

// ── Regime helpers (empirically-derived asymmetric bands, see SPEC) ─────────

const BANDS = [
  { max: 24, label: "Capitulation", regime: "mp1_capitulation", zone: "MP-1" },
  { max: 44, label: "Defensive", regime: "mp2_defensive", zone: "MP-2" },
  { max: 55, label: "Neutral", regime: "mp3_neutral", zone: "MP-3" },
  { max: 75, label: "Risk-On", regime: "mp4_risk_on", zone: "MP-4" },
  { max: 100, label: "Euphoria", regime: "mp5_euphoria", zone: "MP-5" },
];

function band(score: number) {
  return BANDS.find((b) => score <= b.max) ?? BANDS[2];
}

const REGIME_COLORS: Record<string, string> = {
  mp1_capitulation: "#DC2626",
  mp2_defensive: "#F97316",
  mp3_neutral: "#6B7280",
  mp4_risk_on: "#22C55E",
  mp5_euphoria: "#10B981",
};

function titleCase(name: string): string {
  return name
    .split(/[_\s]+/)
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

// ── Dashboard (scores + history) ────────────────────────────────────────────

export interface SubIndex {
  score: number;
  change1d: number;
  change1w: number;
  regime: string;
  label: string;
  confidence: number;
}

export interface Dashboard {
  composite: number;
  regime: string;
  regimeLabel: string;
  direction: string;
  confidence: number;
  explanation: string;
  change1d: number;
  change1w: number;
  subIndices: { classic: SubIndex; narrative: SubIndex; positioning: SubIndex };
  history: HistoryPoint[];
  sp500Level: number;
}

function mapHistory(raw: any): HistoryPoint[] {
  const series: any[] = Array.isArray(raw?.series) ? [...raw.series] : [];
  // API returns most-recent-first; the charts expect ascending order.
  series.sort((a, b) =>
    String(a.timestamp) < String(b.timestamp) ? -1 : 1,
  );
  return series.map((r) => {
    const composite = Math.round(r.composite_score ?? 50);
    return {
      date: String(r.timestamp).slice(0, 10),
      // Raw index levels are intentionally excluded from sanitized exports,
      // so we render an index-level proxy derived from the composite score.
      sp500: 4000 + composite * 8,
      classic: Math.round(r.classic_score ?? 50),
      narrative: Math.round(r.narrative_score ?? 50),
      positioning: Math.round(r.positioning_score ?? 50),
      composite,
      regime: band(composite).regime,
    };
  });
}

export function mockDashboard(): Dashboard {
  const history = MOCK_HISTORY;
  const last = history[history.length - 1];
  const day = history[history.length - 2] ?? last;
  const week = history[history.length - 8] ?? history[0] ?? last;
  const sub = (key: "classic" | "narrative" | "positioning"): SubIndex => {
    const m = MOCK_SUB_INDICES[key];
    return {
      score: m.score,
      change1d: m.change1d,
      change1w: m.change1w,
      regime: m.regime,
      label: m.label,
      confidence: m.confidence,
    };
  };
  return {
    composite: MOCK_COMPOSITE_SCORE,
    regime: MOCK_REGIME,
    regimeLabel: MOCK_REGIME_LABEL,
    direction: MOCK_DIRECTION,
    confidence: MOCK_CONFIDENCE,
    explanation: MOCK_EXPLANATION,
    change1d: last ? last.composite - day.composite : 0,
    change1w: last ? last.composite - week.composite : 0,
    subIndices: {
      classic: sub("classic"),
      narrative: sub("narrative"),
      positioning: sub("positioning"),
    },
    history,
    sp500Level: last?.sp500 ?? 4200,
  };
}

export async function getDashboard(market = "sp500"): Promise<Dashboard> {
  try {
    const [scores, histRaw] = await Promise.all([
      load("scores/current", { market }, `scores-current-${market}`),
      load("history/scores", { market, days: "90" }, `history-scores-${market}`),
    ]);

    const history = mapHistory(histRaw);
    if (history.length === 0) return mockDashboard();

    const n = history.length;
    const last = history[n - 1];
    const day = history[n - 2] ?? last;
    const week = history[n - 8] ?? history[0] ?? last;

    const sub = (
      key: "classic" | "narrative" | "positioning",
      apiScore: number | undefined,
    ): SubIndex => {
      const score = Math.round(apiScore ?? last[key]);
      return {
        score,
        change1d: score - day[key],
        change1w: score - week[key],
        regime: band(score).regime,
        label: band(score).label,
        confidence: Math.round(scores.confidence ?? MOCK_CONFIDENCE),
      };
    };

    const composite = Math.round(scores.composite_score ?? last.composite);
    return {
      composite,
      regime: scores.regime ?? band(composite).regime,
      regimeLabel: scores.regime_label ?? band(composite).label,
      direction: scores.direction ?? "stable",
      confidence: Math.round(scores.confidence ?? MOCK_CONFIDENCE),
      explanation: scores.explanation ?? MOCK_EXPLANATION,
      change1d: composite - day.composite,
      change1w: composite - week.composite,
      subIndices: {
        classic: sub("classic", scores.classic_score),
        narrative: sub("narrative", scores.narrative_score),
        positioning: sub("positioning", scores.positioning_score),
      },
      history,
      sp500Level: last.sp500,
    };
  } catch {
    return mockDashboard();
  }
}

// ── Components ───────────────────────────────────────────────────────────────

export async function getComponents(market = "sp500"): Promise<ComponentData[]> {
  try {
    const raw = await load(
      "components/current",
      { market },
      `components-current-${market}`,
    );
    const comps: any[] = Array.isArray(raw?.components) ? raw.components : [];
    if (comps.length === 0) return MOCK_COMPONENTS;
    return comps.map((c) => {
      const score = Math.round(c.normalized_score ?? c.score ?? 50);
      const weight = c.weight ?? 0.143;
      const direction: ComponentData["direction"] =
        c.direction ?? (score >= 56 ? "bullish" : score <= 44 ? "bearish" : "neutral");
      return {
        name: titleCase(c.name ?? ""),
        score,
        weight,
        contribution: Math.round(score * weight * 10) / 10,
        direction,
        description: c.description ?? "",
      };
    });
  } catch {
    return MOCK_COMPONENTS;
  }
}

// ── Source status ────────────────────────────────────────────────────────────

export async function getSources(): Promise<SourceStatusData[]> {
  try {
    const raw = await load("sources/status", {}, "sources-status");
    const providers: any[] = Array.isArray(raw?.providers) ? raw.providers : [];
    if (providers.length === 0) return MOCK_SOURCES;
    return providers.map((p) => ({
      provider: p.display_name ?? p.provider ?? "Unknown",
      available: Boolean(p.available),
      tier: p.tier ?? "public",
      lastFetch: p.last_successful_fetch
        ? timeAgo(p.last_successful_fetch)
        : "Never",
      dataFreshness:
        p.data_freshness_minutes != null
          ? `${p.data_freshness_minutes} min delay`
          : "N/A",
    }));
  } catch {
    return MOCK_SOURCES;
  }
}

// ── Backtest forward returns ─────────────────────────────────────────────────

export interface ForwardReturnRow {
  regime: string;
  range: string;
  color: string;
  m1: number;
  m3: number;
  m6: number;
  m12: number;
  occurrences: number;
}

export async function getForwardReturns(
  market = "sp500",
): Promise<ForwardReturnRow[]> {
  try {
    const raw = await load(
      "backtest/regimes",
      { market },
      `backtest-regimes-${market}`,
    );
    const regimes: any[] = Array.isArray(raw?.regimes) ? raw.regimes : [];
    if (regimes.length === 0) return FORWARD_RETURNS;
    return regimes.map((r) => {
      const fr = r.forward_returns ?? {};
      const mean = (h: string) => Math.round((fr[h]?.mean ?? 0) * 10) / 10;
      const label = r.regime_label ?? band(50).label;
      // The payload may carry a `regime` code or only a `regime_label`.
      const matched =
        BANDS.find((b) => b.regime === r.regime) ??
        BANDS.find((b) => b.label === label);
      return {
        regime: `${matched?.zone ?? ""} ${label}`.trim(),
        range: r.score_range ?? "",
        color: matched ? REGIME_COLORS[matched.regime] : "#6B7280",
        m1: mean("1m"),
        m3: mean("3m"),
        m6: mean("6m"),
        m12: mean("12m"),
        occurrences: r.periods_analyzed ?? r.occurrences ?? 0,
      };
    });
  } catch {
    return FORWARD_RETURNS;
  }
}

// ── Multi-market comparison (Markets page chart) ─────────────────────────────

const COMPARE: { id: string; label: string }[] = [
  { id: "sp500", label: "S&P 500" },
  { id: "nasdaq100", label: "Nasdaq 100" },
  { id: "russell2000", label: "Russell 2000" },
  { id: "dow", label: "Dow" },
];

export type ComparisonPoint = { date: string } & Record<string, number | string>;

export async function getMarketComparison(): Promise<ComparisonPoint[]> {
  try {
    const histories = await Promise.all(
      COMPARE.map((m) =>
        load("history/scores", { market: m.id, days: "90" }, `history-scores-${m.id}`)
          .then(mapHistory)
          .catch(() => [] as HistoryPoint[]),
      ),
    );
    const base = histories[0];
    if (!base || base.length === 0) return mockComparison();
    const tail = (h: HistoryPoint[]) => h.slice(-30);
    const cols = histories.map(tail);
    return tail(base).map((point, i) => {
      const row: ComparisonPoint = { date: point.date };
      COMPARE.forEach((m, idx) => {
        row[m.label] = cols[idx]?.[i]?.composite ?? point.composite;
      });
      return row;
    });
  } catch {
    return mockComparison();
  }
}

function mockComparison(): ComparisonPoint[] {
  return MOCK_HISTORY.slice(-30).map((h) => ({
    date: h.date,
    "S&P 500": h.composite,
    "Nasdaq 100": Math.min(100, h.composite + 5),
    "Russell 2000": Math.max(0, h.composite - 10),
    Dow: Math.min(100, h.composite + 1),
  }));
}

export const MARKET_LIST = MARKET_CONFIGS;
