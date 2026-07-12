import { FlowerSprite } from "@/components/ui/FlowerSprite";

export function About() {
  return (
    <section id="about" className="relative py-32 px-6 md:px-12 w-full bg-[var(--bg-dream)] overflow-hidden">
      {/* Subtle Flower Decoration */}
      <div className="absolute top-10 right-10 w-[150px] h-[150px] opacity-[0.08] rotate-12 pointer-events-none">
        <FlowerSprite className="w-full h-full" flowerIndex={5} />
      </div>
      <div className="absolute bottom-10 left-10 w-[120px] h-[120px] opacity-[0.1] -rotate-12 pointer-events-none">
        <FlowerSprite className="w-full h-full" flowerIndex={7} />
      </div>

      <div className="max-w-2xl mx-auto relative z-10 text-center">
        <h2 className="font-display text-3xl mb-8 text-[var(--ink)]">About GlazeSmith</h2>
        
        <div className="space-y-6 text-[var(--ink-soft)] leading-relaxed text-left text-lg">
          <p>
            GlazeSmith is a hybrid computational engine for evaluating and optimizing ceramic glaze stability. It enforces a strict separation between deterministic thermodynamic math and machine learning, avoiding the pitfalls of asking neural networks to guess at fundamental physics.
          </p>
          <p>
            The system processes formulations through a six-layer decoupled pipeline: deterministic physics for thermal expansion, XGBoost classification for surface and color, K-NN vector retrieval for real-world analogues, Pareto optimization, SDXL for visual representation, and an LLM-based interpretation loop.
          </p>
          <p>
            This project was built for the AMD Unicorn Track Hackathon. It leverages AMD ROCm MI300X hardware to co-locate graph neural network inference, vector search, and image generation in VRAM, while using Fireworks AI for fast LLM communication.
          </p>
        </div>
      </div>
    </section>
  );
}
