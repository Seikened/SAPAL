// hooks/use-poll.ts
"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { API } from "@/lib/api";

export function usePoll<T>(path: string, intervalMs = 10_000) {
  const [data, setData] = useState<T | null>(null);
  const ctrlRef = useRef<AbortController | null>(null);

  const refetch = useCallback(async () => {
    try {
      ctrlRef.current?.abort();
      const ctrl = new AbortController();
      ctrlRef.current = ctrl;

      const url = path.startsWith("http") ? path : `${API}${path}`;
      const res = await fetch(url, { cache: "no-store", signal: ctrl.signal });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const json = (await res.json()) as T;
      setData(json);
    } catch {
      /* ignore */
    }
  }, [path]);

  useEffect(() => {
    refetch();
    const id = setInterval(refetch, intervalMs);
    return () => {
      clearInterval(id);
      ctrlRef.current?.abort();
    };
  }, [refetch, intervalMs]);

  return { data, refetch, setData };
}