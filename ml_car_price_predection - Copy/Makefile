# Makefile for ML Car Price Prediction Project

.PHONY: help install test train predict clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make train         - Train model"
	@echo "  make predict       - Run batch inference"
	@echo "  make clean         - Clean generated files"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest src/tests/ -v --cov=src --cov-report=html

train:
	python -m src.pipelines.training_pipeline --model-type random_forest --n-estimators 100

predict:
	python -m src.pipelines.inference_pipeline --input data/testset/test.csv --output predictions.csv

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker-compose -f deployment/dev/docker-compose.dev.yml build

docker-up:
	docker-compose -f deployment/dev/docker-compose.dev.yml up -d

docker-down:
	docker-compose -f deployment/dev/docker-compose.dev.yml down

format:
	black src/
	isort src/

lint:
	flake8 src/
	pylint src/
