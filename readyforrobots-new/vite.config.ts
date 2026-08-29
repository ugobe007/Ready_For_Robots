import { jsxLocPlugin } from "@builder.io/vite-plugin-jsx-loc";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { defineConfig, loadEnv, type Plugin, type ViteDevServer } from "vite";
import { vitePluginManusRuntime } from "vite-plugin-manus-runtime";

// =============================================================================
// Manus Debug Collector - Vite Plugin
// Writes browser logs directly to files, trimmed when exceeding size limit
// =============================================================================

const PROJECT_ROOT = import.meta.dirname;
const CLIENT_ROOT = path.resolve(PROJECT_ROOT, "client");
const APP_DATA_ROOT = path.resolve(PROJECT_ROOT, "..", "app", "data");
const LOG_DIR = path.join(PROJECT_ROOT, ".manus-logs");
const MAX_LOG_SIZE_BYTES = 1 * 1024 * 1024; // 1MB per log file
const TRIM_TARGET_BYTES = Math.floor(MAX_LOG_SIZE_BYTES * 0.6); // Trim to 60% to avoid constant re-trimming

type LogSource = "browserConsole" | "networkRequests" | "sessionReplay";

/** Injects FastAPI base for `getApiBase()` (same idea as Next `_app.js` meta). */
function injectRfrApiMeta(): Plugin {
  return {
    name: "inject-rfr-api-meta",
    transformIndexHtml(html) {
      if (html.includes('name="rfr-api-base"')) return html;
      const raw = (process.env.VITE_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
      if (!raw) return html;
      return html.replace("<head>", `<head>\n    <meta name="rfr-api-base" content="${raw}" />`);
    },
  };
}

function rfrReleaseId(): string {
  const envSha = (
    process.env.VERCEL_GIT_COMMIT_SHA ||
    process.env.GITHUB_SHA ||
    process.env.VITE_RFR_RELEASE ||
    ""
  ).trim();
  if (envSha) return `git-${envSha.slice(0, 12)}`;
  try {
    const sha = execSync("git rev-parse --short=12 HEAD", {
      cwd: path.resolve(PROJECT_ROOT, ".."),
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    if (/^[0-9a-f]{7,12}$/i.test(sha)) return `git-${sha}`;
  } catch {
    /* git missing in the build image */
  }
  return "git-dev";
}

/** Homepage meta must move with the git SHA so production does not look frozen. */
function injectRfrReleaseMeta(): Plugin {
  return {
    name: "inject-rfr-release-meta",
    transformIndexHtml(html) {
      const id = rfrReleaseId().replace(/[^a-zA-Z0-9._-]/g, "");
      if (!id) return html;
      if (html.includes('name="rfr-release"')) {
        return html.replace(
          /<meta\s+name="rfr-release"\s+content="[^"]*"\s*\/>/,
          `<meta name="rfr-release" content="${id}" />`,
        );
      }
      return html.replace(
        "<head>",
        `<head>\n    <meta name="rfr-release" content="${id}" />`,
      );
    },
  };
}

/** Fail production builds that would ship a dead /signup (null supabase client). */
function requirePublicSupabaseEnv(): Plugin {
  return {
    name: "require-public-supabase-env",
    configResolved(config) {
      if (config.command !== "build" || config.mode !== "production") return;
      const fileEnv = loadEnv(config.mode, config.envDir || PROJECT_ROOT, "VITE_");
      const url =
        process.env.VITE_PUBLIC_SUPABASE_URL || fileEnv.VITE_PUBLIC_SUPABASE_URL || "";
      const key =
        process.env.VITE_PUBLIC_SUPABASE_ANON_KEY ||
        fileEnv.VITE_PUBLIC_SUPABASE_ANON_KEY ||
        process.env.VITE_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
        fileEnv.VITE_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
        "";
      if (!url.includes("supabase.co") || key.length < 20) {
        throw new Error(
          "Production Vite build requires VITE_PUBLIC_SUPABASE_URL and " +
            "VITE_PUBLIC_SUPABASE_ANON_KEY (or VITE_PUBLIC_SUPABASE_PUBLISHABLE_KEY). " +
            "Without them /signup Google and GitHub buttons do nothing. " +
            "Set them in .github/workflows/deploy-frontend.yml (same values as fly.toml [build.args]).",
        );
      }
    },
  };
}

function ensureLogDir() {
  if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
  }
}

function trimLogFile(logPath: string, maxSize: number) {
  try {
    if (!fs.existsSync(logPath) || fs.statSync(logPath).size <= maxSize) {
      return;
    }

    const lines = fs.readFileSync(logPath, "utf-8").split("\n");
    const keptLines: string[] = [];
    let keptBytes = 0;

    // Keep newest lines (from end) that fit within 60% of maxSize
    const targetSize = TRIM_TARGET_BYTES;
    for (let i = lines.length - 1; i >= 0; i--) {
      const lineBytes = Buffer.byteLength(`${lines[i]}\n`, "utf-8");
      if (keptBytes + lineBytes > targetSize) break;
      keptLines.unshift(lines[i]);
      keptBytes += lineBytes;
    }

    fs.writeFileSync(logPath, keptLines.join("\n"), "utf-8");
  } catch {
    /* ignore trim errors */
  }
}

function writeToLogFile(source: LogSource, entries: unknown[]) {
  if (entries.length === 0) return;

  ensureLogDir();
  const logPath = path.join(LOG_DIR, `${source}.log`);

  // Format entries with timestamps
  const lines = entries.map((entry) => {
    const ts = new Date().toISOString();
    return `[${ts}] ${JSON.stringify(entry)}`;
  });

  // Append to log file
  fs.appendFileSync(logPath, `${lines.join("\n")}\n`, "utf-8");

  // Trim if exceeds max size
  trimLogFile(logPath, MAX_LOG_SIZE_BYTES);
}

/**
 * Vite plugin to collect browser debug logs
 * - POST /__manus__/logs: Browser sends logs, written directly to files
 * - Files: browserConsole.log, networkRequests.log, sessionReplay.log
 * - Auto-trimmed when exceeding 1MB (keeps newest entries)
 */
function vitePluginManusDebugCollector(): Plugin {
  return {
    name: "manus-debug-collector",

    transformIndexHtml(html) {
      if (process.env.NODE_ENV === "production") {
        return html;
      }
      return {
        html,
        tags: [
          {
            tag: "script",
            attrs: {
              src: "/__manus__/debug-collector.js",
              defer: true,
            },
            injectTo: "head",
          },
        ],
      };
    },

    configureServer(server: ViteDevServer) {
      // POST /__manus__/logs: Browser sends logs (written directly to files)
      server.middlewares.use("/__manus__/logs", (req, res, next) => {
        if (req.method !== "POST") {
          return next();
        }

        const handlePayload = (payload: any) => {
          // Write logs directly to files
          if (payload.consoleLogs?.length > 0) {
            writeToLogFile("browserConsole", payload.consoleLogs);
          }
          if (payload.networkRequests?.length > 0) {
            writeToLogFile("networkRequests", payload.networkRequests);
          }
          if (payload.sessionEvents?.length > 0) {
            writeToLogFile("sessionReplay", payload.sessionEvents);
          }

          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ success: true }));
        };

        const reqBody = (req as { body?: unknown }).body;
        if (reqBody && typeof reqBody === "object") {
          try {
            handlePayload(reqBody);
          } catch (e) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ success: false, error: String(e) }));
          }
          return;
        }

        let body = "";
        req.on("data", (chunk) => {
          body += chunk.toString();
        });

        req.on("end", () => {
          try {
            const payload = JSON.parse(body);
            handlePayload(payload);
          } catch (e) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ success: false, error: String(e) }));
          }
        });
      });
    },
  };
}

function vitePluginStorageProxy(): Plugin {
  return {
    name: "manus-storage-proxy",
    configureServer(server: ViteDevServer) {
      server.middlewares.use("/manus-storage", async (req, res) => {
        const key = req.url?.replace(/^\//, "");
        if (!key) {
          res.writeHead(400, { "Content-Type": "text/plain" });
          res.end("Missing storage key");
          return;
        }

        const forgeBaseUrl = (process.env.BUILT_IN_FORGE_API_URL || "").replace(/\/+$/, "");
        const forgeKey = process.env.BUILT_IN_FORGE_API_KEY;

        if (!forgeBaseUrl || !forgeKey) {
          res.writeHead(500, { "Content-Type": "text/plain" });
          res.end("Storage proxy not configured");
          return;
        }

        try {
          const forgeUrl = new URL("v1/storage/presign/get", forgeBaseUrl + "/");
          forgeUrl.searchParams.set("path", key);

          const forgeResp = await fetch(forgeUrl, {
            headers: { Authorization: `Bearer ${forgeKey}` },
          });

          if (!forgeResp.ok) {
            res.writeHead(502, { "Content-Type": "text/plain" });
            res.end("Storage backend error");
            return;
          }

          const { url } = (await forgeResp.json()) as { url: string };
          if (!url) {
            res.writeHead(502, { "Content-Type": "text/plain" });
            res.end("Empty signed URL");
            return;
          }

          res.writeHead(307, { Location: url, "Cache-Control": "no-store" });
          res.end();
        } catch {
          res.writeHead(502, { "Content-Type": "text/plain" });
          res.end("Storage proxy error");
        }
      });
    },
  };
}

const isDev = process.env.NODE_ENV !== "production";

const plugins = [
  injectRfrApiMeta(),
  injectRfrReleaseMeta(),
  requirePublicSupabaseEnv(),
  react(),
  tailwindcss(),
  jsxLocPlugin(),
  ...(isDev ? [vitePluginManusRuntime(), vitePluginManusDebugCollector(), vitePluginStorageProxy()] : []),
];

export default defineConfig({
  plugins,
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "client", "src"),
      "@shared": path.resolve(import.meta.dirname, "shared"),
      "@assets": path.resolve(import.meta.dirname, "attached_assets"),
      "@ontology": path.resolve(import.meta.dirname, "client", "src", "lib", "industry_sector_ontology.json"),
    },
  },
  envDir: path.resolve(import.meta.dirname),
  root: path.resolve(import.meta.dirname, "client"),
  build: {
    outDir: path.resolve(import.meta.dirname, "dist/public"),
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    strictPort: false, // Will find next available port if 3000 is busy
    host: true,
    allowedHosts: [
      ".manuspre.computer",
      ".manus.computer",
      ".manus-asia.computer",
      ".manuscomputer.ai",
      ".manusvm.computer",
      "localhost",
      "127.0.0.1",
    ],
    fs: {
      strict: true,
      deny: ["**/.*"],
      // Custom allow replaces defaults in Vite 7 — must include client root + repo app/data.
      allow: [PROJECT_ROOT, CLIENT_ROOT, APP_DATA_ROOT],
    },
  },
});
