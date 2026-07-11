import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import type { Plugin } from "vite"
import { inspectAttr } from 'plugin-inspect-react-code'

// Strips OneDrive/SharePoint "mso" document-tracking metadata that gets
// auto-injected into index.html inside synced folders, so it never leaks
// an internal SharePoint URL / DocId into the built output.
const stripOfficeMetadata: Plugin = {
  name: "strip-office-metadata",
  transformIndexHtml(html) {
    return html
      .replace(/<!--\[if gte mso[\s\S]*?<!\[endif\]-->/gi, "")
      .replace(/ xmlns:mso="[^"]*"/gi, "")
      .replace(/ xmlns:msdt="[^"]*"/gi, "")
  },
}

// https://vite.dev/config/
export default defineConfig({
  base: '/MarketPulse/',
  plugins: [stripOfficeMetadata, inspectAttr(), react()],
  server: {
    port: 3000,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
