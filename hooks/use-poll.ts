// hooks/use-poll.ts
"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export function usePoll<T>(path: string, ms = 10_000) {
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    let alive = true;
    const fetcher = async () => {
      try {
        const d = await apiGet<T>(path, { cache: "no-store" });
        if (alive) setData(d);
      } catch {
        /* noop */
      }
    };
    fetcher();
    const id = setInterval(fetcher, ms);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [path, ms]);

  return data;
}
