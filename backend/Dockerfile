FROM rocm/pytorch:rocm6.3.2_ubuntu24.04_py3.12_pytorch_release_2.4.0

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings openai pandas pyarrow Pillow httpx python-multipart

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
