// hooks/use-sse.ts
"use client";
import { useEffect } from "react";

export function useSSE(onMessage: (data: any) => void) {
  useEffect(() => {
    const src = new EventSource("/sim/events/stream", { withCredentials: false });
    const handler = (ev: MessageEvent) => {
      try { onMessage(JSON.parse(ev.data)); } catch { /* noop */ }
    };
    src.addEventListener("message", handler as any);
    return () => src.close();
  }, [onMessage]);
}