from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.predict import router as predict_router
from .config import settings

app = FastAPI(
    title="GlazeSmith API",
    description="AI agent for ceramic glaze formulation, defect diagnosis, and image generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "device": "amd_rocm"}
