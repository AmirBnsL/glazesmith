import { cn } from "@/lib/utils";

interface FlowerSpriteProps {
  className?: string;
  flowerIndex?: number; // 0-8 for the 3x3 grid
}

export function FlowerSprite({ className }: FlowerSpriteProps) {
  return (
    <div 
      className={cn("bg-no-repeat", className)} 
      style={{
        backgroundImage: "url('/assets/flower.svg')",
        backgroundSize: "contain",
        backgroundPosition: "center",
      }}
    />
  );
}
