.PHONY: up down test migrate lint format install-hooks dev-setup clean logs changelog

up:
	docker compose up --build -d

down:
	docker compose down

test:
	cd backend && pytest -v

migrate:
	cd backend && alembic upgrade head

lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff check --fix . && ruff format .

install-hooks:
	pre-commit install

dev-setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r backend/requirements-dev.txt
	.venv/bin/pip install pre-commit
	.venv/bin/pre-commit install
	cp -n .env.example .env || true
	cd frontend && npm install
	@echo "✅ Fejlesztői környezet kész!"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	rm -f *.db
	@echo "✅ Tisztítás kész!"

logs:
	docker compose logs -f --tail=100

changelog:
	git-cliff -o CHANGELOG.md
	@echo "✅ CHANGELOG.md frissítve!"

# --- Maintenance ---
maintenance-health:
	./scripts/maintenance.sh health

maintenance-backup:
	./scripts/maintenance.sh backup

maintenance-daily:
	./scripts/maintenance.sh full-daily

maintenance-weekly:
	./scripts/maintenance.sh full-weekly

maintenance-monthly:
	./scripts/maintenance.sh full-monthly

install-cron:
	sudo ./scripts/setup-cron.sh
