PYTHON := ./.venv/bin/python
TOPIC ?= AI Agent Framework
CONTRACT_TESTS := tests/test_writer_agent_artifacts.py tests/test_orchestrator_smoke.py

.PHONY: install test js-test run freeze ci contract smoke

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -U pytest

test:
	$(PYTHON) -m pytest -q

js-test:
	node --test tests/workflow_app_utils.test.js tests/workflow_security_regression.test.js

run:
	$(PYTHON) -m agents.research "$(TOPIC)"

freeze:
	$(PYTHON) -m pip freeze > requirements.lock.txt

contract:
	$(PYTHON) -m pytest -q $(CONTRACT_TESTS)

ci: test js-test contract

smoke:
	$(PYTHON) -m agents.research "CI Smoke"
