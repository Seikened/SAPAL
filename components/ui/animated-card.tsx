// components/ui/animated-card.tsx
"use client";
import { motion, useReducedMotion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Level = "normal" | "warning" | "critical";

const variants = {
  normal: {
    scale: 1,
    boxShadow: "0 0 0px rgba(0,0,0,0)",
    transition: { duration: 0.4, ease: "easeOut" },
  },
  warning: {
    scale: [1, 1.01, 1],
    boxShadow: [
      "0 0 0px rgba(251,191,36,0.0)",
      "0 0 14px rgba(251,191,36,0.35)",
      "0 0 0px rgba(251,191,36,0.0)",
    ],
    transition: { duration: 1.6, repeat: Infinity, ease: "easeInOut" },
  },
  critical: {
    scale: [1, 1.02, 1],
    boxShadow: [
      "0 0 0px rgba(239,68,68,0.0)",
      "0 0 18px rgba(239,68,68,0.55)",
      "0 0 0px rgba(239,68,68,0.0)",
    ],
    transition: { duration: 1.1, repeat: Infinity, ease: "easeInOut" },
  },
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

  // Si el usuario prefiere menos animación, dejamos todo quieto.
  const current = prefersReduced ? "normal" : level;

  return (
    <motion.div
      role={role}
      aria-label={ariaLabel}
      className={cn("outline-none focus-visible:ring-2 focus-visible:ring-primary/60 rounded-2xl", className)}
      initial={false}
      animate={current as keyof typeof variants}
      variants={variants as any}
      whileHover={!prefersReduced && level !== "normal" ? { scale: 1.025 } : undefined}
      onClick={onClick}
    >
      <Card className="rounded-2xl">{children}</Card>
    </motion.div>
  );
}
