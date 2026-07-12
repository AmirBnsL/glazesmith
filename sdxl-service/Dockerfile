# SDXL image generation service — runs on AMD Instinct GPU via ROCm
# Base image: ROCm 6.3.2 + PyTorch 2.4 (HIP backend)
# Target hardware: AMD Instinct MI300X (192 GB HBM3)
# GPU passthrough configured in docker-compose.yml (/dev/kfd, /dev/dri)
FROM rocm/pytorch:rocm6.3.2_ubuntu24.04_py3.12_pytorch_release_2.4.0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
