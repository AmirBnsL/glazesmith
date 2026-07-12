"use client";

import { FlowerSprite } from "@/components/ui/FlowerSprite";
import { ThemeSwitcher } from "./ThemeSwitcher";
import { Menu } from "lucide-react";
import { useState } from "react";

export function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setMenuOpen(false);
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-16 z-50 px-6 md:px-12 flex items-center justify-between transition-all duration-300 backdrop-blur-md bg-[var(--bg-dream)]/40 border-b border-[var(--ink)]/5">
      <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
        <FlowerSprite className="w-6 h-6 opacity-90 drop-shadow-sm" flowerIndex={4} />
        <span className="font-accent text-3xl text-[var(--ink)] tracking-wide pt-1">GlazeSmith</span>
      </div>
      
      {/* Desktop Nav */}
      <div className="hidden sm:flex items-center gap-6">
        <button onClick={() => scrollTo("app")} className="text-[var(--ink-soft)] hover:text-[var(--ink)] transition-colors font-medium text-sm">
          App
        </button>
        <button onClick={() => scrollTo("about")} className="rounded-full border border-[var(--ink-soft)]/30 px-4 py-1.5 text-sm font-medium text-[var(--ink)] hover:bg-[var(--ink)]/5 transition-colors">
          About
        </button>
        <ThemeSwitcher />
      </div>

      {/* Mobile Nav */}
      <div className="flex sm:hidden items-center gap-3">
        <ThemeSwitcher />
        <button onClick={() => setMenuOpen(!menuOpen)} className="p-2 text-[var(--ink)]">
          <Menu className="w-5 h-5" />
        </button>
      </div>
      
      {/* Mobile Menu Dropdown */}
      {menuOpen && (
        <div className="absolute top-16 left-0 right-0 bg-[var(--bg-dream)]/95 backdrop-blur-xl border-b border-[var(--ink)]/5 p-4 flex flex-col gap-4 sm:hidden shadow-lg">
          <button onClick={() => scrollTo("app")} className="text-left px-4 py-2 text-[var(--ink-soft)] hover:text-[var(--ink)]">
            App
          </button>
          <button onClick={() => scrollTo("about")} className="text-left px-4 py-2 text-[var(--ink-soft)] hover:text-[var(--ink)]">
            About
          </button>
        </div>
      )}
    </header>
  );
}
