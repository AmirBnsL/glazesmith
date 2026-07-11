.PHONY: build up down logs test train clean

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose exec backend python -m pytest

train:
	.venv/bin/python -m backend.training.train_production

# Run without SDXL (CPU-only, no GPU required)
up-lite:
	docker compose up -d

# Full stack with SDXL on GPU
up-full:
	docker compose up -d --profile full

clean:
	docker compose down -v --rmi local
	rm -rf sdxl-service/__pycache__

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d
