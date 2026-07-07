"use client";

interface Props {
  imageUrl: string | null;
  loading: boolean;
}

export default function GlazePreview({ imageUrl, loading }: Props) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-amber-400">Fired Glaze Preview</h3>
      <div className="bg-stone-800 rounded-xl border border-stone-700 aspect-square flex items-center justify-center overflow-hidden">
        {loading && (
          <div className="text-stone-500 text-sm animate-pulse">Generating preview...</div>
        )}
        {!loading && imageUrl && (
          <img src={imageUrl} alt="Glaze preview" className="w-full h-full object-cover" />
        )}
        {!loading && !imageUrl && (
          <div className="text-stone-600 text-xs text-center px-4">
            Enter a recipe and run prediction to see the fired glaze preview
          </div>
        )}
      </div>
    </div>
  );
}
