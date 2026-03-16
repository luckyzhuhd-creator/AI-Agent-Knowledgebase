PYTHON := ./.venv/bin/python
TOPIC ?= AI Agent Framework

.PHONY: install test run freeze ci contract smoke

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -U pytest

test:
	$(PYTHON) -m pytest -q

run:
	$(PYTHON) -m agents.research "$(TOPIC)"

freeze:
	$(PYTHON) -m pip freeze > requirements.lock.txt

contract:
	$(PYTHON) -m pytest -q tests/test_writer_agent_artifacts.py tests/test_orchestrator_smoke.py

ci: test contract

smoke:
	$(PYTHON) -m agents.research "CI Smoke"