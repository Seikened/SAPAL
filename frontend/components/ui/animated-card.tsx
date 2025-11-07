"use client";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

type Level = "normal" | "warning" | "critical";

const palette = {
  normal:  { rgb: "34,197,94",  bg: "rgba(34,197,94,0.12)"  }, // emerald-500
  warning: { rgb: "234,179,8",  bg: "rgba(234,179,8,0.16)"  }, // amber-500
  critical:{ rgb: "239,68,68",  bg: "rgba(239,68,68,0.18)"  }, // red-500
};

const variants = {
  normal: (rgb: string) => ({
    scale: 1,
    boxShadow: `inset 0 0 0 2px rgba(${rgb},0.35), 0 0 0 rgba(0,0,0,0)`,
    transition: { duration: 0.3, ease: "easeOut" },
  }),
  warning: (rgb: string) => ({
    scale: [1, 1.03, 1],
    boxShadow: [
      `inset 0 0 0 2px rgba(${rgb},0.35), 0 0 0 rgba(${rgb},0.00)`,
      `inset 0 0 0 3px rgba(${rgb},0.70), 0 0 36px rgba(${rgb},0.42)`,
      `inset 0 0 0 2px rgba(${rgb},0.35), 0 0 0 rgba(${rgb},0.00)`,
    ],
    transition: { duration: 1.2, repeat: Infinity, ease: "easeInOut" },
  }),
  critical: (rgb: string) => ({
    scale: [1, 1.05, 1],
    boxShadow: [
      `inset 0 0 0 2px rgba(${rgb},0.50), 0 0 0 rgba(${rgb},0.00)`,
      `inset 0 0 0 4px rgba(${rgb},0.90), 0 0 46px rgba(${rgb},0.55)`,
      `inset 0 0 0 2px rgba(${rgb},0.50), 0 0 0 rgba(${rgb},0.00)`,
    ],
    transition: { duration: 1.0, repeat: Infinity, ease: "easeInOut" },
  }),
};

export function AnimatedCard({
  level,
  className,
  children,
  onClick,
  role = "button",
  "aria-label": ariaLabel,
}: {
  level: Level;
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
  role?: string;
  "aria-label"?: string;
}) {
  const prefersReduced = useReducedMotion();
  const { rgb, bg } = palette[level];
  const animatedKey = prefersReduced ? "normal" : level;

  return (
    <motion.div
      role={role}
      aria-label={ariaLabel}
      className={cn(
        // one animated layer = no “static border” desync
        "rounded-2xl p-4 backdrop-blur-[0.5px] outline-none",
        "focus-visible:ring-2 focus-visible:ring-primary/60",
        className
      )}
      style={{
        backgroundColor: bg,              // subtle fill per state
        borderRadius: 16,                 // match rounded-2xl
      }}
      initial={{ opacity: 0.98, scale: 0.985 }}
      animate={variants[animatedKey as Level](rgb)}
      whileHover={!prefersReduced ? { scale: 1.02 } : undefined}
      transition={{ type: "tween" }}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}
