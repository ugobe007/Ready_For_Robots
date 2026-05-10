import { Link } from "wouter";
import { getApiBase } from "@/lib/apiBase";

/** Minimal shell — full admin UI can be ported from legacy Next `admin.js` later. */
export default function Admin() {
  const api = getApiBase();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: "#0d0520" }}>
      <div className="max-w-md text-center space-y-4">
        <h1 className="text-xl font-bold text-white" style={{ fontFamily: "'Sora', system-ui" }}>
          Admin
        </h1>
        <p className="text-sm text-white/50">FastAPI admin routes and docs live on the API host.</p>
        <a
          href={`${api}/api/docs`}
          target="_blank"
          rel="noreferrer"
          className="inline-block rounded-lg px-4 py-2 text-sm font-semibold text-white"
          style={{ background: "#7c3aed" }}
        >
          Open API docs
        </a>
        <div>
          <Link href="/" className="text-xs text-white/40 hover:text-white/70">
            ← Home
          </Link>
        </div>
      </div>
    </div>
  );
}
