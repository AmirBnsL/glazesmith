"use client";

import { useState } from "react";
import type { RecipeIngredient } from "@/lib/types";

const KNOWN_MATERIALS = [
  "Nepheline Syenite", "Custer Feldspar", "Potash Feldspar",
  "Silica (325 mesh)", "Whiting", "EPK Kaolin", "Kaolin",
  "Gillespie Borate", "Gerstley Borate", "Dolomite", "Zinc Oxide",
  "Red Iron Oxide", "Titanium Dioxide", "Bentonite", "Lithium Carbonate",
];

interface Props {
  recipe: RecipeIngredient[];
  onChange: (recipe: RecipeIngredient[]) => void;
}

export default function RecipeGrid({ recipe, onChange }: Props) {
  const addRow = () => {
    onChange([...recipe, { material: "", percentage: 0 }]);
  };

  const updateRow = (i: number, field: keyof RecipeIngredient, value: string) => {
    const next = [...recipe];
    if (field === "percentage") {
      next[i] = { ...next[i], percentage: parseFloat(value) || 0 };
    } else {
      next[i] = { ...next[i], material: value };
    }
    onChange(next);
  };

  const removeRow = (i: number) => {
    onChange(recipe.filter((_, idx) => idx !== i));
  };

  const total = recipe.reduce((s, r) => s + r.percentage, 0);
  const valid = Math.abs(total - 100) < 1;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-amber-400">Recipe</h3>
        <span className={`text-xs ${valid ? "text-green-400" : "text-red-400"}`}>
          {total.toFixed(1)}%
        </span>
      </div>

      <div className="space-y-1">
        {recipe.map((row, i) => (
          <div key={i} className="flex gap-1">
            <select
              className="flex-1 bg-stone-800 rounded px-2 py-1 text-sm text-stone-100"
              value={row.material}
              onChange={(e) => updateRow(i, "material", e.target.value)}
            >
              <option value="">Select material...</option>
              {KNOWN_MATERIALS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <input
              className="w-20 bg-stone-800 rounded px-2 py-1 text-sm text-stone-100 text-right"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={row.percentage || ""}
              onChange={(e) => updateRow(i, "percentage", e.target.value)}
            />
            <button
              className="text-stone-500 hover:text-red-400 px-1"
              onClick={() => removeRow(i)}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <button
        className="text-xs text-amber-500 hover:text-amber-400"
        onClick={addRow}
      >
        + Add material
      </button>
    </div>
  );
}
