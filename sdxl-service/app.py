"""SDXL image generation service for GlazeSmith.

Runs on AMD ROCm GPU (MI300X). Loads Stable Diffusion XL on startup
using PyTorch with ROCm/HIP backend, generates ceramic glaze
visualizations from text prompts.

Hardware: AMD Instinct MI300X (192 GB HBM3) via ROCm 6.3
Framework: PyTorch 2.4 with ROCm backend (torch.version.hip)
Model: stabilityai/stable-diffusion-xl-base-1.0 (FP16, ~7 GB VRAM)
"""

import io
import uuid
import torch
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from diffusers import StableDiffusionXLPipeline
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGES_DIR = Path("/app/images")
IMAGES_DIR.mkdir(exist_ok=True)

pipeline: StableDiffusionXLPipeline | None = None


def get_device_info() -> dict:
    """Detect AMD ROCm GPU vs CUDA vs CPU."""
    if torch.cuda.is_available():
        hip_version = getattr(torch.version, "hip", None)
        if hip_version:
            # Running on AMD ROCm (HIP maps to CUDA API)
            gpu_name = torch.cuda.get_device_name(0)
            return {
                "device": "rocm",
                "hip_version": hip_version,
                "gpu": gpu_name,
                "vram_gb": round(torch.cuda.get_device_properties(0).total_mem / 1e9, 1),
            }
        else:
            gpu_name = torch.cuda.get_device_name(0)
            return {"device": "cuda", "gpu": gpu_name}
    return {"device": "cpu"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    device_info = get_device_info()
    logger.info("Detected device: %s", device_info)

    if device_info["device"] == "rocm":
        logger.info(
            "AMD ROCm GPU detected: %s (HIP %s, %.1f GB VRAM)",
            device_info["gpu"], device_info["hip_version"], device_info["vram_gb"],
        )
    elif device_info["device"] == "cuda":
        logger.info("NVIDIA CUDA GPU detected: %s", device_info["gpu"])
    else:
        logger.warning("No GPU detected — SDXL will run on CPU (very slow)")

    logger.info("Loading SDXL model...")
    try:
        pipe = StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
        )
        if torch.cuda.is_available():
            # On ROCm, torch.cuda maps to HIP — "cuda" device works for both
            pipe = pipe.to("cuda")
            logger.info("SDXL loaded on GPU (%s)", device_info["device"].upper())
        else:
            logger.warning("SDXL loaded on CPU — will be slow")
        pipeline = pipe
    except Exception as e:
        logger.error("Failed to load SDXL: %s", e)
        pipeline = None
    yield


app = FastAPI(title="GlazeSmith SDXL", version="1.0.0", lifespan=lifespan)


class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = "ugly, blurry, low quality, deformed"


class GenerateResponse(BaseModel):
    image_url: str
    success: bool


@app.get("/health")
async def health():
    device_info = get_device_info()
    return {
        "status": "ok",
        "model_loaded": pipeline is not None,
        **device_info,
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="SDXL model not loaded")

    image_id = str(uuid.uuid4())
    output_path = IMAGES_DIR / f"{image_id}.png"

    try:
        result = pipeline(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            num_inference_steps=30,
            guidance_scale=7.5,
        )
        result.images[0].save(output_path)
        logger.info("Generated image %s", image_id)
        return GenerateResponse(image_url=f"/images/{image_id}.png", success=True)
    except Exception as e:
        logger.error("Generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/images/{filename}")
async def serve_image(filename: str):
    filepath = IMAGES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath, media_type="image/png")
