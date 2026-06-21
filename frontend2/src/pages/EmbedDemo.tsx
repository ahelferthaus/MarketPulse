import { useState } from "react";
import { Copy, Check, Code2, Globe, FileJson } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import EmbedWidget from "../components/EmbedWidget";
import { EMBED_CODES } from "../lib/mockData";

export default function EmbedDemo() {
  const [size, setSize] = useState<"small" | "medium" | "full">("medium");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [copied, setCopied] = useState<string | null>(null);

  const handleCopy = (type: string, code: string) => {
    navigator.clipboard.writeText(code).catch(() => {});
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <section className="py-8 md:py-10 px-4 md:px-8" style={{ backgroundColor: "#0A1628" }}>
        <div className="max-w-7xl mx-auto text-center">
          <Code2 size={36} className="mx-auto mb-3 text-emerald-400" />
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-2">
            Embed MarketPulse
          </h1>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">
            Add MarketPulse to your website or application with a simple
            embed code.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 py-8 space-y-8">
        {/* Controls */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
            {/* Size toggle */}
            <div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block mb-2">
                Size
              </span>
              <div className="flex rounded-lg border border-slate-200 overflow-hidden">
                {(["small", "medium", "full"] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setSize(s)}
                    className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
                      size === s
                        ? "bg-slate-800 text-white"
                        : "bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Theme toggle */}
            <div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block mb-2">
                Theme
              </span>
              <div className="flex rounded-lg border border-slate-200 overflow-hidden">
                {(["light", "dark"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTheme(t)}
                    className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
                      theme === t
                        ? "bg-slate-800 text-white"
                        : "bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Live Preview */}
        <div>
          <h2 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
            <Globe size={18} />
            Live Preview
          </h2>
          <div
            className={`rounded-xl border-2 border-dashed border-slate-200 p-8 flex justify-center ${
              theme === "dark" ? "bg-slate-900" : "bg-slate-50"
            }`}
          >
            <EmbedWidget size={size} theme={theme} />
          </div>
        </div>

        {/* Embed Code */}
        <div>
          <h2 className="text-base font-bold text-slate-800 mb-3">
            Embed Code
          </h2>
          <Tabs defaultValue="iframe" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="iframe" className="text-xs">
                <Code2 size={14} className="mr-1" />
                HTML iframe
              </TabsTrigger>
              <TabsTrigger value="javascript" className="text-xs">
                <Code2 size={14} className="mr-1" />
                JavaScript
              </TabsTrigger>
              <TabsTrigger value="json" className="text-xs">
                <FileJson size={14} className="mr-1" />
                JSON API
              </TabsTrigger>
            </TabsList>

            <TabsContent value="iframe">
              <CodeBlock
                code={EMBED_CODES.iframe}
                copied={copied === "iframe"}
                onCopy={() => handleCopy("iframe", EMBED_CODES.iframe)}
              />
            </TabsContent>
            <TabsContent value="javascript">
              <CodeBlock
                code={EMBED_CODES.javascript}
                copied={copied === "javascript"}
                onCopy={() => handleCopy("javascript", EMBED_CODES.javascript)}
              />
            </TabsContent>
            <TabsContent value="json">
              <CodeBlock
                code={EMBED_CODES.json}
                copied={copied === "json"}
                onCopy={() => handleCopy("json", EMBED_CODES.json)}
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Usage Guidelines */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h2 className="text-base font-bold text-slate-800 mb-3">
            Usage Guidelines
          </h2>
          <ul className="space-y-2 text-sm text-slate-600">
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">&bull;</span>
              The iframe is the easiest option — just copy and paste into your HTML.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">&bull;</span>
              Use the JavaScript embed for dynamic sizing and custom styling hooks.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">&bull;</span>
              The JSON API returns raw data for fully custom implementations.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">&bull;</span>
              All embeds are responsive and work on mobile, tablet, and desktop.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">&bull;</span>
              Please include the "Powered by Westwood MarketPulse" attribution.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}

function CodeBlock({
  code,
  copied,
  onCopy,
}: {
  code: string;
  copied: boolean;
  onCopy: () => void;
}) {
  return (
    <div className="relative">
      <pre className="bg-slate-900 text-slate-200 rounded-lg p-4 text-xs overflow-x-auto leading-relaxed font-mono">
        {code}
      </pre>
      <Button
        variant="outline"
        size="sm"
        onClick={onCopy}
        className="absolute top-2 right-2 bg-white/10 border-white/20 text-white hover:bg-white/20 text-xs"
      >
        {copied ? <Check size={14} className="mr-1" /> : <Copy size={14} className="mr-1" />}
        {copied ? "Copied" : "Copy"}
      </Button>
    </div>
  );
}
