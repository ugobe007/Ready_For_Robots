import { useEffect, useState } from "react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { mapApiNextActions } from "@/lib/pipelineNextActions";
import type { NextAction } from "@/types/readyForRobots";

export function usePipelineNextActions(limit = 3) {
  const [actions, setActions] = useState<NextAction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(
      `${getApiBase()}/api/leads/pipeline-next-actions?limit=${limit}`,
      liveFetchInit()
    )
      .then(res => (res.ok ? res.json() : null))
      .then(data => {
        if (!cancelled) setActions(mapApiNextActions(data));
      })
      .catch(() => {
        if (!cancelled) setActions([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [limit]);

  return { actions, loading };
}
