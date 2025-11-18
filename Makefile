.PHONY: help build up down logs clean restart

help:
	@echo "Money Trading Bot - Development Commands"
	@echo ""
	@echo "make build    - Build Docker containers"
	@echo "make up       - Start all services"
	@echo "make down     - Stop all services"
	@echo "make logs     - View logs"
	@echo "make clean    - Remove containers and volumes"
	@echo "make restart  - Restart all services"
	@echo "make test     - Run tests"
	@echo "make shell    - Open backend shell"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	rm -rf backend/__pycache__
	rm -rf frontend/.next
	rm -rf frontend/node_modules

restart:
	docker-compose restart

test:
	docker-compose exec backend pytest tests/

shell:
	docker-compose exec backend /bin/bash

migrate:
	docker-compose exec backend alembic upgrade head

makemigrations:
	docker-compose exec backend alembic revision --autogenerate -m "Auto migration"

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn src.main:app --reload

dev-frontend:
	cd frontend && npm run dev

celery-worker:
	cd backend && celery -A src.tasks.celery_app worker --loglevel=info

celery-beat:
	cd backend && celery -A src.tasks.celery_app beat --loglevel=info
