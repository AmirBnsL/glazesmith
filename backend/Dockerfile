# Backend runs on CPU — XGBoost inference (<10ms) and Faiss K-NN don't need GPU.
# GPU workloads (SDXL image generation) run on the separate sdxl-service
# container which uses the ROCm PyTorch base image (see sdxl-service/Dockerfile).
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
