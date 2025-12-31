# ===========================================
# Stock Tracker - Makefile
# ===========================================

.PHONY: help up down logs backend frontend db-shell test lint

help:
	@echo "Comandos disponíveis:"
	@echo "  make up        - Inicia todos os containers"
	@echo "  make down      - Para todos os containers"
	@echo "  make logs      - Mostra logs de todos os containers"
	@echo "  make backend   - Logs do backend"
	@echo "  make frontend  - Logs do frontend"
	@echo "  make db-shell  - Abre shell do PostgreSQL"
	@echo "  make test      - Roda os testes"
	@echo "  make lint      - Roda o linter"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

backend:
	docker-compose logs -f backend

frontend:
	docker-compose logs -f frontend

db-shell:
	docker-compose exec db psql -U stocktracker -d stock_tracker

test:
	cd backend && pytest

lint:
	cd backend && ruff check .
