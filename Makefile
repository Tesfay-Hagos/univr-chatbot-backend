# Install dependencies using uv package manager
install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.8.13/install.sh | sh; source $HOME/.local/bin/env; }
	uv sync

# Install with Jupyter support
install-jupyter:
	uv sync --extra jupyter

# Install with dev dependencies
install-dev:
	uv sync --extra dev

# Run the FastAPI development server
dev:
	@echo "==============================================================================="
	@echo "| 🚀 Starting UniVR Chatbot development server...                            |"
	@echo "==============================================================================="
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run the FastAPI server (production mode)
run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run code quality checks
lint:
	uv sync --extra dev
	uv run ruff check . --diff
	uv run ruff format . --check --diff

# Auto-fix linting issues
lint-fix:
	uv run ruff check . --fix
	uv run ruff format .

# Run tests
test:
	uv run pytest

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Frontend (Next.js) commands
install-frontend:
	cd frontend && npm install

frontend-dev:
	@echo "==============================================================================="
	@echo "| 🎨 Starting Next.js frontend development server...                         |"
	@echo "==============================================================================="
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-start:
	cd frontend && npm run start

frontend-lint:
	cd frontend && npm run lint

# Run both backend and frontend in parallel (requires running in separate terminals)
dev-all:
	@echo "==============================================================================="
	@echo "| 🚀 Starting both backend and frontend servers...                           |"
	@echo "| Run 'make dev' in one terminal and 'make frontend-dev' in another.         |"
	@echo "==============================================================================="
	@echo "Tip: Use 'make dev' and 'make frontend-dev' in separate terminals."

.PHONY: install install-jupyter install-dev dev run lint lint-fix test clean install-frontend frontend-dev frontend-build frontend-start frontend-lint dev-all
