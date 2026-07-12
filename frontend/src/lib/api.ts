import type { PredictRequest, PredictResponse, GenerateImageRequest, GenerateImageResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function predictGlaze(req: PredictRequest): Promise<PredictResponse> {
  const res = await fetch(`${BASE}/api/predict-glaze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error (${res.status}): ${err}`);
  }
  return res.json();
}

export async function generateImage(req: GenerateImageRequest): Promise<GenerateImageResponse> {
  const res = await fetch(`${BASE}/api/generate-image`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Image gen error (${res.status}): ${err}`);
  }
  return res.json();
}

export async function chatWithAgent(req: import("./types").ChatRequest): Promise<import("./types").ChatResponse> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Chat API error (${res.status}): ${err}`);
  }
  return res.json();
}
