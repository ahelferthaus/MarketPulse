// ===== SCORES =====
export const MOCK_COMPOSITE_SCORE = 67;
export const MOCK_REGIME = "mp4_risk_on";
export const MOCK_REGIME_LABEL = "Risk-On";
export const MOCK_DIRECTION = "rising";
export const MOCK_CONFIDENCE = 85;
export const MOCK_EXPLANATION =
  "Markets are risk-on, driven by strong momentum and positioning, though narrative sentiment has cooled.";
export const MOCK_WHAT_CHANGED =
  "Narrative sentiment cooled 5 points after Fed policy comments, while positioning strengthened on ETF inflows.";
export const MOCK_WHY_IT_MATTERS =
  "Risk-on conditions suggest investors are comfortable with current valuations, but cooling narrative sentiment warrants watching for shifts in Fed expectations.";

export const MOCK_SUB_INDICES = {
  classic: {
    score: 72,
    change1d: 3,
    change1w: -5,
    regime: "mp4_risk_on",
    label: "Risk-On",
    confidence: 92,
  },
  narrative: {
    score: 58,
    change1d: -2,
    change1w: 8,
    regime: "mp3_neutral",
    label: "Neutral",
    confidence: 78,
  },
  positioning: {
    score: 71,
    change1d: 1,
    change1w: -3,
    regime: "mp4_risk_on",
    label: "Risk-On",
    confidence: 85,
  },
};

// ===== HISTORY (90 days) =====
export interface HistoryPoint {
  date: string;
  sp500: number;
  classic: number;
  narrative: number;
  positioning: number;
  composite: number;
  regime: string;
}

function generateHistory(): HistoryPoint[] {
  const points: HistoryPoint[] = [];
  const baseDate = new Date("2026-01-15");
  for (let i = 89; i >= 0; i--) {
    const date = new Date(baseDate);
    date.setDate(date.getDate() - i);
    const t = i / 89;
    const sp500 =
      4200 +
      Math.sin(t * Math.PI * 2) * 200 +
      (1 - t) * 150 +
      Math.random() * 30;
    const classic = 50 + Math.sin(t * Math.PI * 3) * 25 + Math.random() * 5;
    const narrative =
      45 + Math.cos(t * Math.PI * 2.5) * 20 + Math.random() * 8;
    const positioning =
      55 + Math.sin(t * Math.PI * 2 + 1) * 22 + Math.random() * 6;
    const composite =
      classic * 0.4 + narrative * 0.3 + positioning * 0.3;
    // Empirically-derived asymmetric regime thresholds
    const regime =
      composite > 75
        ? "mp5"
        : composite > 55
          ? "mp4"
          : composite > 44
            ? "mp3"
            : composite > 24
              ? "mp2"
              : "mp1";
    points.push({
      date: date.toISOString().split("T")[0],
      sp500: Math.round(sp500 * 100) / 100,
      classic: Math.round(Math.max(0, Math.min(100, classic))),
      narrative: Math.round(Math.max(0, Math.min(100, narrative))),
      positioning: Math.round(Math.max(0, Math.min(100, positioning))),
      composite: Math.round(Math.max(0, Math.min(100, composite))),
      regime,
    });
  }
  return points;
}
export const MOCK_HISTORY = generateHistory();

// ===== COMPONENTS =====
export interface ComponentData {
  name: string;
  score: number;
  weight: number;
  contribution: number;
  direction: "bullish" | "bearish" | "neutral";
  description: string;
}

export const MOCK_COMPONENTS: ComponentData[] = [
  {
    name: "Momentum",
    score: 78,
    weight: 0.143,
    contribution: 11.1,
    direction: "bullish",
    description: "Price vs 125-day moving average",
  },
  {
    name: "Breadth",
    score: 65,
    weight: 0.143,
    contribution: 9.3,
    direction: "bullish",
    description: "Advancing/declining volume ratio",
  },
  {
    name: "Put/Call",
    score: 82,
    weight: 0.143,
    contribution: 11.7,
    direction: "bullish",
    description: "Put/call ratio (inverted)",
  },
  {
    name: "Credit Spreads",
    score: 70,
    weight: 0.143,
    contribution: 10.0,
    direction: "bullish",
    description: "High-yield OAS spread",
  },
  {
    name: "Volatility",
    score: 68,
    weight: 0.143,
    contribution: 9.7,
    direction: "bullish",
    description: "VIX level (inverted)",
  },
  {
    name: "Safe Haven",
    score: 71,
    weight: 0.143,
    contribution: 10.1,
    direction: "bullish",
    description: "Equity vs safe-haven returns",
  },
  {
    name: "Price Strength",
    score: 69,
    weight: 0.143,
    contribution: 9.9,
    direction: "bullish",
    description: "New highs vs new lows",
  },
];

// ===== SOURCES =====
export interface SourceStatusData {
  provider: string;
  available: boolean;
  tier: string;
  lastFetch: string;
  dataFreshness: string;
}

export const MOCK_SOURCES: SourceStatusData[] = [
  {
    provider: "Yahoo Finance",
    available: true,
    tier: "public",
    lastFetch: "2 min ago",
    dataFreshness: "15 min delay",
  },
  {
    provider: "FRED",
    available: true,
    tier: "public",
    lastFetch: "5 min ago",
    dataFreshness: "Daily",
  },
  {
    provider: "CBOE",
    available: true,
    tier: "public",
    lastFetch: "1 min ago",
    dataFreshness: "Daily close",
  },
  {
    provider: "RSS News",
    available: true,
    tier: "public",
    lastFetch: "3 min ago",
    dataFreshness: "15 min delay",
  },
  {
    provider: "FMP",
    available: false,
    tier: "premium",
    lastFetch: "Never",
    dataFreshness: "N/A",
  },
  {
    provider: "Bloomberg MCP",
    available: false,
    tier: "professional",
    lastFetch: "Never",
    dataFreshness: "N/A",
  },
];

// ===== REGIME DEFINITIONS =====
// Empirically-derived asymmetric ranges based on historical frequency analysis:
// MP-1: 0-24 (~8%), MP-2: 25-44 (~23%), MP-3: 45-55 (~38%),
// MP-4: 56-75 (~24%), MP-5: 76-100 (~7%)
export const REGIME_DEFINITIONS = [
  {
    zone: "MP-1",
    range: "0-24",
    label: "Capitulation",
    color: "#B3382E",
    description:
      "Extreme risk-off conditions. Panic selling, broad-based declines. ~8% frequency.",
  },
  {
    zone: "MP-2",
    range: "25-44",
    label: "Defensive",
    color: "#C4791F",
    description: "Risk-off, defensive positioning. Hedging activity elevated. ~23% frequency.",
  },
  {
    zone: "MP-3",
    range: "45-55",
    label: "Neutral",
    color: "#8B93A1",
    description:
      "Balanced, mixed signals. Neither fear nor greed dominates. ~38% frequency.",
  },
  {
    zone: "MP-4",
    range: "56-75",
    label: "Risk-On",
    color: "#6F9A3D",
    description:
      "Risk-on, constructive. Momentum and positioning support upside. ~24% frequency.",
  },
  {
    zone: "MP-5",
    range: "76-100",
    label: "Euphoria",
    color: "#1F7A4D",
    description:
      "Extreme risk-on, euphoric. Complacency high, bubble risk elevated. ~7% frequency.",
  },
];

// ===== MARKET CONFIGS =====
export const MARKET_CONFIGS = [
  { id: "sp500", name: "S&P 500", ticker: "^GSPC", etf: "SPY", vix: "^VIX" },
  { id: "nasdaq100", name: "Nasdaq 100", ticker: "^NDX", etf: "QQQ", vix: "^VXN" },
  { id: "russell2000", name: "Russell 2000", ticker: "^RUT", etf: "IWM", vix: "^RVX" },
  { id: "dow", name: "Dow Jones", ticker: "^DJI", etf: "DIA", vix: "^VXD" },
];

// ===== FORWARD RETURNS =====
// Updated with empirically-derived asymmetric score ranges
export const FORWARD_RETURNS = [
  {
    regime: "MP-1 Capitulation",
    range: "0-24",
    color: "#B3382E",
    m1: -2.1,
    m3: 3.5,
    m6: 8.2,
    m12: 15.1,
    occurrences: 12,
  },
  {
    regime: "MP-2 Defensive",
    range: "25-44",
    color: "#C4791F",
    m1: -0.5,
    m3: 2.1,
    m6: 5.8,
    m12: 11.3,
    occurrences: 28,
  },
  {
    regime: "MP-3 Neutral",
    range: "45-55",
    color: "#8B93A1",
    m1: 0.8,
    m3: 2.8,
    m6: 6.1,
    m12: 12.5,
    occurrences: 45,
  },
  {
    regime: "MP-4 Risk-On",
    range: "56-75",
    color: "#6F9A3D",
    m1: 1.2,
    m3: 3.5,
    m6: 7.8,
    m12: 14.2,
    occurrences: 38,
  },
  {
    regime: "MP-5 Euphoria",
    range: "76-100",
    color: "#1F7A4D",
    m1: -0.3,
    m3: 1.2,
    m6: 4.5,
    m12: 9.8,
    occurrences: 8,
  },
];

// ===== ARTICLES =====
export interface ArticleData {
  id: number;
  timestamp: string;
  source: string;
  title: string;
  sentiment: number;
  topics: string[];
}

export const MOCK_ARTICLES: ArticleData[] = [
  {
    id: 1,
    timestamp: "2026-01-15T14:30:00Z",
    source: "Reuters",
    title: "Fed officials signal patience on rate cuts as inflation persists",
    sentiment: 42,
    topics: ["fed", "inflation"],
  },
  {
    id: 2,
    timestamp: "2026-01-15T13:15:00Z",
    source: "Bloomberg",
    title: "S&P 500 extends rally as tech earnings beat expectations",
    sentiment: 68,
    topics: ["earnings", "tech"],
  },
  {
    id: 3,
    timestamp: "2026-01-15T12:00:00Z",
    source: "MarketWatch",
    title: "Investors hedging geopolitical risk ahead of election cycle",
    sentiment: 35,
    topics: ["geopolitics", "macro"],
  },
  {
    id: 4,
    timestamp: "2026-01-15T11:30:00Z",
    source: "CNBC",
    title: "Consumer spending remains resilient despite rate headwinds",
    sentiment: 62,
    topics: ["consumer", "macro"],
  },
  {
    id: 5,
    timestamp: "2026-01-15T10:45:00Z",
    source: "WSJ",
    title: "Credit spreads tighten as corporate bond demand surges",
    sentiment: 72,
    topics: ["credit"],
  },
  {
    id: 6,
    timestamp: "2026-01-15T09:20:00Z",
    source: "Financial Times",
    title: "AI investment boom drives semiconductor sector optimism",
    sentiment: 78,
    topics: ["ai_tech", "earnings"],
  },
  {
    id: 7,
    timestamp: "2026-01-15T08:00:00Z",
    source: "Yahoo Finance",
    title: "Market volatility edges lower ahead of holiday weekend",
    sentiment: 55,
    topics: ["macro"],
  },
  {
    id: 8,
    timestamp: "2026-01-14T16:30:00Z",
    source: "Reuters",
    title: "Treasury yields climb on stronger-than-expected jobs data",
    sentiment: 48,
    topics: ["fed", "macro"],
  },
];

// ===== LOG ENTRIES =====
export const MOCK_LOG_ENTRIES = [
  "[2026-01-15 16:30:01] INFO: Daily update started for sp500",
  "[2026-01-15 16:30:02] INFO: Yahoo Finance provider connected",
  "[2026-01-15 16:30:03] INFO: Fetched 1260 days of price history for SPY",
  "[2026-01-15 16:30:04] INFO: FRED provider connected",
  "[2026-01-15 16:30:05] WARN: FMP provider unavailable, using fallback",
  "[2026-01-15 16:30:06] INFO: CBOE data fetched: put/call = 0.82",
  "[2026-01-15 16:30:07] INFO: RSS news: 8 articles ingested",
  "[2026-01-15 16:30:08] INFO: Classic score calculated: 72.3",
  "[2026-01-15 16:30:09] INFO: Narrative score calculated: 58.1",
  "[2026-01-15 16:30:10] INFO: Positioning score calculated: 70.8",
  "[2026-01-15 16:30:11] INFO: Composite score: 67.4 (Risk-On)",
  "[2026-01-15 16:30:12] INFO: Export generated successfully",
];

// ===== REGIME TRANSITIONS =====
export const REGIME_TRANSITIONS = [
  { from: "MP-3 Neutral", to: "MP-4 Risk-On", count: 18 },
  { from: "MP-4 Risk-On", to: "MP-3 Neutral", count: 12 },
  { from: "MP-4 Risk-On", to: "MP-5 Euphoria", count: 6 },
  { from: "MP-2 Defensive", to: "MP-3 Neutral", count: 15 },
  { from: "MP-3 Neutral", to: "MP-2 Defensive", count: 10 },
  { from: "MP-5 Euphoria", to: "MP-4 Risk-On", count: 5 },
  { from: "MP-1 Capitulation", to: "MP-2 Defensive", count: 8 },
  { from: "MP-2 Defensive", to: "MP-1 Capitulation", count: 4 },
];

// ===== EMBED WIDGET =====
export const EMBED_CODES = {
  iframe: `<iframe\n  src="https://marketpulse.westwood.com/embed?market=sp500&size=medium&theme=light"\n  width="600"\n  height="400"\n  frameborder="0"\n  title="Westwood MarketPulse"\n></iframe>`,
  javascript: `<div id="marketpulse-widget"></div>\n<script\n  src="https://marketpulse.westwood.com/embed.js"\n  data-market="sp500"\n  data-size="medium"\n  data-theme="light"\n  data-target="marketpulse-widget"\n></script>`,
  json: `fetch('https://marketpulse.westwood.com/api/v1/embed/marketpulse.json?market=sp500')\n  .then(r => r.json())\n  .then(data => {\n    console.log('Composite score:', data.composite_score);\n  });`,
};
