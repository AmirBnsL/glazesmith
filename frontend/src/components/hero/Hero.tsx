"use client";

import { Suspense, lazy } from "react";
import { CloudBackground } from "./CloudBackground";
import { FlowerScatter } from "./FlowerScatter";

// Use lazy loading for canvas to avoid SSR issues
const VaseCanvas = lazy(() => import("./VaseCanvas"));

export function Hero() {
  return (
    <section id="hero" className="relative isolate min-h-screen flex items-center justify-center overflow-hidden bg-[var(--bg-dream)]">
      <CloudBackground />
      <FlowerScatter />
      
      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center pt-16">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] md:w-[450px] md:h-[450px] bg-[var(--flower-petal)]/30 blur-[80px] rounded-full z-5 pointer-events-none" />
        <div className="absolute inset-0 z-10">
          <Suspense fallback={<div className="w-full h-full flex items-center justify-center text-[var(--ink-soft)] animate-pulse">Loading 3D Model...</div>}>
            <VaseCanvas />
          </Suspense>
        </div>
        
        {/* Minimal Hero Copy */}
        {/* <div className="absolute bottom-4 md:bottom-8 text-center px-4">
          <h1 className="font-display text-2xl md:text-3xl text-[var(--ink)] tracking-wide">GlazeSmith</h1>
          <p className="text-[var(--ink-soft)] text-sm md:text-base mt-1 max-w-[280px]">Ceramic glaze formulation & AI diagnostics</p>
        </div> */}
      </div>
    </section>
  );
}
