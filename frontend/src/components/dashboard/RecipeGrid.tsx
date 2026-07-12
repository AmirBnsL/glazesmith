"use client";

import { useState } from "react";
import type { RecipeIngredient } from "@/lib/types";
import type { RecipeRow } from "./AppDashboard";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";

const KNOWN_MATERIALS = [
  "Nepheline Syenite", "Custer Feldspar", "Potash Feldspar",
  "Silica (325 mesh)", "Whiting", "EPK Kaolin", "Kaolin",
  "Gillespie Borate", "Gerstley Borate", "Dolomite", "Zinc Oxide",
  "Red Iron Oxide", "Titanium Dioxide", "Bentonite", "Lithium Carbonate",
];

interface Props {
  recipe: RecipeRow[];
  onChange: (recipe: RecipeRow[]) => void;
}

export default function RecipeGrid({ recipe, onChange }: Props) {
  const addRow = () => {
    onChange([...recipe, { id: crypto.randomUUID(), material: "", percentage: 0 }]);
  };

  const updateRow = (id: string, field: keyof RecipeIngredient, value: string) => {
    onChange(recipe.map(row => {
      if (row.id !== id) return row;
      if (field === "percentage") {
        return { ...row, percentage: parseFloat(value) || 0 };
      }
      return { ...row, material: value };
    }));
  };

  const removeRow = (id: string) => {
    onChange(recipe.filter(row => row.id !== id));
  };

  const total = recipe.reduce((s, r) => s + r.percentage, 0);
  const valid = Math.abs(total - 100) < 1;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--ink)]">Recipe</h3>
        <span className={`text-xs font-medium ${valid ? "text-green-600 " : "text-amber-600 "}`}>
          {total.toFixed(1)}%
        </span>
      </div>

      <div className="space-y-1">
        {recipe.map((row) => (
          <div key={row.id} className="flex gap-1 items-center">
            <Select value={row.material} onValueChange={(val) => updateRow(row.id, "material", val as string)}>
              <SelectTrigger className="flex-1 bg-white/40 border-[var(--ink-soft)]/20 text-[var(--ink)] text-sm h-9 rounded-lg">
                <SelectValue placeholder="Select material..." />
              </SelectTrigger>
              <SelectContent>
                {KNOWN_MATERIALS.map((m) => (
                  <SelectItem key={m} value={m}>{m}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={row.percentage || ""}
              onChange={(e) => updateRow(row.id, "percentage", e.target.value)}
              className="w-20 bg-white/40 border-[var(--ink-soft)]/20 text-[var(--ink)] text-sm h-9 rounded-lg text-right"
            />
            <button
              className="text-[var(--ink-soft)] hover:text-red-500 transition-colors px-2 rounded-lg"
              onClick={() => removeRow(row.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <button
        className="w-full mt-2 rounded-full border border-[var(--ink-soft)]/30 px-4 py-1.5 text-sm font-medium text-[var(--ink)] hover:bg-[var(--glaze-glass)] transition-colors"
        onClick={addRow}
      >
        + Add material
      </button>
    </div>
  );
}
