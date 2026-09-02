.PHONY: install run lint format

install:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --port 8000

lint:
	ruff check app

format:
	ruff format app
