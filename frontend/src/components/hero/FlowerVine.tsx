"use client";

import { FlowerSprite } from "@/components/ui/FlowerSprite";

interface FlowerVineProps {
  x: number;
  y: number;
  
  // Flower specific tweaks
  flowerScale?: number;
  flowerRotation?: number;
  flowerX?: number;
  flowerY?: number;

  // Trunk specific tweaks
  trunkScale?: number;
  trunkRotation?: number;
  trunkX?: number;
  trunkY?: number;

  stemPath?: string;
  leafPaths?: string[];
}

export function FlowerVine({ 
  x, y, 
  flowerScale = 1, flowerRotation = 0, flowerX = 0, flowerY = 0,
  trunkScale = 1, trunkRotation = 0, trunkX = 16, trunkY = 32, // Defaults to top-8 (32px) left-4 (16px)
  stemPath, leafPaths = [] 
}: FlowerVineProps) {

  // For the new cropped SVG, we don't need random flower indexing anymore.
  return (
    <div
      className="absolute"
      style={{ left: x, top: y }}
    >
      <div className="relative w-32 h-40">
        {/* TRUNK LAYER */}
        <svg 
          viewBox="0 0 120 160" 
          className="absolute -z-10 w-full h-full opacity-70 overflow-visible"
          style={{ 
            left: trunkX, top: trunkY, 
            transform: `scale(${trunkScale}) rotate(${trunkRotation}deg)`
          }}
        >
          {stemPath && (
            <path
              d={stemPath}
              stroke="var(--stem-green)"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
            />
          )}
          {leafPaths.map((path, i) => (
            <path
              key={i}
              d={path}
              stroke="var(--stem-green)"
              strokeWidth="1.5"
              strokeLinecap="round"
              fill="none"
            />
          ))}
        </svg>

        {/* FLOWER LAYER */}
        <div 
          className="absolute w-24 h-24"
          style={{ 
            left: flowerX, top: flowerY,
            transform: `scale(${flowerScale}) rotate(${flowerRotation}deg)` 
          }}
        >
          <FlowerSprite className="w-full h-full drop-shadow-sm" />
        </div>
      </div>
    </div>
  );
}
