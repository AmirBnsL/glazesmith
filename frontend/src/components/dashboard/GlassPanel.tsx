import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import React from "react";

export function GlassPanel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <Card className={cn(
      "rounded-2xl bg-[var(--glaze-glass)] border border-white/40 shadow-[0_8px_32px_rgba(242,141,160,0.15)] p-5",
      className
    )}>
      {children}
    </Card>
  );
}
