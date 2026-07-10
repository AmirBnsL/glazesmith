"""SDXL image generation service for GlazeSmith.

Runs on AMD ROCm GPU. Loads SDXL model on startup,
generates ceramic glaze visualizations from prompts.
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    logger.info("Loading SDXL model...")
    try:
        pipe = StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
        )
        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
            logger.info("SDXL loaded on GPU")
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
    return {
        "status": "ok",
        "model_loaded": pipeline is not None,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
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
