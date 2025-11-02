// components/sparkline.tsx
"use client";
import React from "react";

export function Sparkline({
  data,
  className,
  strokeWidth = 2,
  height = 28,
}: {
  data: number[];
  className?: string;
  strokeWidth?: number;
  height?: number;
}) {
  if (!data || data.length < 2) return null;
  const w = 120;
  const h = height;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const norm = (v: number) =>
    max === min ? h / 2 : h - ((v - min) / (max - min)) * h;

  const step = w / (data.length - 1);
  const d = data
    .map((v, i) => `${i === 0 ? "M" : "L"} ${i * step},${norm(v)}`)
    .join(" ");

  const last = data[data.length - 1];
  const prev = data[data.length - 2];
  const up = last > prev + 1e-6;
  const down = last < prev - 1e-6;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={className} aria-hidden>
      <path d={d} fill="none" stroke="currentColor" strokeWidth={strokeWidth} />
      <circle cx={w} cy={norm(last)} r={3} fill="currentColor" />
      <title>
        {up ? "Subiendo" : down ? "Bajando" : "Estable"} — último: {last.toFixed(3)}
      </title>
    </svg>
  );
}