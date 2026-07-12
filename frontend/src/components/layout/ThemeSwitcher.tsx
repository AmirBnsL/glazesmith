"use client";

import { useTheme } from "next-themes";
import { Palette, Check } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  const themes = [
    { id: "light", label: "Light" },
    { id: "kiln", label: "Kiln Amber" },
    { id: "plum", label: "Midnight Plum" },
    { id: "indigo", label: "Indigo Night" },
  ];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="p-2 rounded-full border border-[var(--ink-soft)]/30 text-[var(--ink)] hover:bg-[var(--ink)]/5 transition-colors flex items-center justify-center">
        <Palette className="w-4 h-4" />
        <span className="sr-only">Switch theme</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-[var(--bg-dream)]/95 backdrop-blur-xl border border-[var(--ink-soft)]/20 shadow-lg min-w-[160px]">
        {themes.map((t) => (
          <DropdownMenuItem
            key={t.id}
            onClick={() => setTheme(t.id)}
            className="flex items-center justify-between cursor-pointer text-[var(--ink)] focus:bg-[var(--ink-soft)]/20 focus:text-[var(--ink)] data-[highlighted]:bg-[var(--ink-soft)]/20"
          >
            <span>{t.label}</span>
            {theme === t.id && <Check className="w-4 h-4 text-[var(--ink)]" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
