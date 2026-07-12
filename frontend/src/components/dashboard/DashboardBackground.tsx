import { FlowerSprite } from "@/components/ui/FlowerSprite";

export function DashboardBackground() {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden bg-gradient-to-br from-[var(--bg-dream-2)] to-[var(--bg-dream)]">
      {/* Color Blobs */}
      <div className="absolute top-[10%] left-[20%] w-[400px] h-[400px] rounded-full bg-[var(--flower-petal)] blur-[100px] opacity-20" />
      <div className="absolute top-[60%] right-[15%] w-[500px] h-[500px] rounded-full bg-[var(--ink-soft)] blur-[120px] opacity-15" />
      
      {/* Flower Textures */}
      <div className="absolute top-[8%] right-[40%] w-[80px] h-[80px] opacity-[0.08] rotate-12">
        <FlowerSprite className="w-full h-full" flowerIndex={1} />
      </div>
      <div className="absolute top-[35%] left-[25%] w-[60px] h-[60px] opacity-[0.14] -rotate-12">
        <FlowerSprite className="w-full h-full" flowerIndex={2} />
      </div>
      <div className="absolute bottom-[45%] right-[20%] w-[110px] h-[110px] opacity-[0.06] rotate-45">
        <FlowerSprite className="w-full h-full" flowerIndex={3} />
      </div>
      <div className="absolute bottom-[15%] left-[35%] w-[90px] h-[90px] opacity-[0.12] -rotate-45">
        <FlowerSprite className="w-full h-full" flowerIndex={8} />
      </div>
      <div className="absolute top-[20%] left-[5%] w-[70px] h-[70px] opacity-[0.09] rotate-[60deg]">
        <FlowerSprite className="w-full h-full" flowerIndex={4} />
      </div>
      <div className="absolute bottom-[30%] right-[5%] w-[100px] h-[100px] opacity-[0.11] -rotate-[30deg]">
        <FlowerSprite className="w-full h-full" flowerIndex={5} />
      </div>
      <div className="absolute top-[60%] left-[10%] w-[50px] h-[50px] opacity-[0.13] rotate-[15deg]">
        <FlowerSprite className="w-full h-full" flowerIndex={6} />
      </div>
      <div className="absolute bottom-[5%] right-[60%] w-[85px] h-[85px] opacity-[0.07] -rotate-[75deg]">
        <FlowerSprite className="w-full h-full" flowerIndex={7} />
      </div>
      <div className="absolute top-[50%] right-[5%] w-[65px] h-[65px] opacity-[0.10] rotate-[85deg]">
        <FlowerSprite className="w-full h-full" flowerIndex={0} />
      </div>
      <div className="absolute top-[5%] left-[45%] w-[95px] h-[95px] opacity-[0.08] -rotate-[50deg]">
        <FlowerSprite className="w-full h-full" flowerIndex={2} />
      </div>
    </div>
  );
}
