import { FlowerVine } from "./FlowerVine";

// EDIT THIS ARRAY TO PLACE FLOWERS EXACTLY HOW YOU WANT
const FLOWER_CONFIG = [
  // --- TOP LEFT CLUSTER ---
  {
    group: "left",
    x: 0, y: 0,
    flowerScale: 1.2, flowerRotation: -15, flowerX: 0, flowerY: 100,
    trunkScale: 2, trunkRotation: 180, trunkX: -40, trunkY: -5,
    stemPath: "M60 160 C 40 120, 70 90, 50 40",
    leafPaths: [],
  },
  {
    group: "left",
    x: 60, y: 40,
    flowerScale: 0.9, flowerRotation: 25, flowerX: -130, flowerY: 150,
    trunkScale: 2, trunkRotation: -175, trunkX: -190, trunkY: 32,
    stemPath: "M1000 260 Q 0 500, 35 40",
    leafPaths: [],
  },
  {
    group: "left",
    x: 20, y: 100,
    flowerScale: 0.7, flowerRotation: -45, flowerX: 5, flowerY: 90,
    trunkScale: 1.5, trunkRotation: -30, trunkX: -33, trunkY: -50,
    stemPath: "M40 160 C 20 130, 50 100, 30 50",
    leafPaths: [],
  },

  // --- BOTTOM RIGHT CLUSTER (Mirrored y=x) ---
  {
    group: "right",
    x: 0, y: 0,
    flowerScale: 1.2, flowerRotation: 105, flowerX: 0, flowerY: -200,
    trunkScale: 2, trunkRotation: -90, trunkX: 40, trunkY: -40,
    stemPath: "M160 60 C 120 40, 90 70, 40 50",
    leafPaths: [],
  },
  {
    group: "right",
    x: -60, y: -40,
    flowerScale: 0.9, flowerRotation: -65, flowerX: 0, flowerY: -80,
    trunkScale: 2, trunkRotation: 265, trunkX: 32, trunkY: -190,
    stemPath: "M-260 70 Q -70 90, 30 50",
    leafPaths: [],
  },
  {
    group: "right",
    x: 100, y: 20,
    flowerScale: 0.7, flowerRotation: 135, flowerX: 90, flowerY: 5,
    trunkScale: 1.5, trunkRotation: 120, trunkX: -50, trunkY: -33,
    stemPath: "M160 40 C 130 20, 100 50, 50 30",
    leafPaths: [],
  },
];

export function FlowerScatter() {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
      {/* Top Left Cluster */}
      <div className="absolute top-10 left-[-20px] md:left-10 lg:left-20 origin-top-left scale-75 md:scale-100">
        {FLOWER_CONFIG.filter((f) => f.group === "left").map((config, i) => (
          <FlowerVine key={`left-${i}`} {...config} />
        ))}
      </div>

      {/* Bottom Right Cluster */}
      <div className="absolute bottom-10 right-10 md:right-32 origin-bottom-right scale-75 md:scale-100">
        {FLOWER_CONFIG.filter((f) => f.group === "right").map((config, i) => (
          <FlowerVine key={`right-${i}`} {...config} />
        ))}
      </div>
    </div>
  );
}
