import { useEffect, useState } from "react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

export type PipelineStats = {
  hot: number | null;
  warm: number | null;
  total: number | null;
  loading: boolean;
};

export function usePipelineStats(): PipelineStats {
  const [hot, setHot] = useState<number | null>(null);
  const [warm, setWarm] = useState<number | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${getApiBase()}/api/leads/summary?exclude_junk=true`,
          liveFetchInit(),
        );
        if (!res.ok || cancelled) return;
        const data = (await res.json()) as { hot?: number; warm?: number; total?: number };
        if (cancelled) return;
        const h = Number(data.hot ?? 0);
        const w = Number(data.warm ?? 0);
        const t = Number(data.total ?? 0) || h + w;
        if (h > 0) setHot(h);
        if (w > 0) setWarm(w);
        if (t > 0) setTotal(t);
      } catch {
        /* keep null fallbacks */
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { hot, warm, total, loading };
}

export function formatStat(n: number | null, fallback: string): string {
  if (n == null || n <= 0) return fallback;
  return n.toLocaleString();
}
