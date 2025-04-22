PACKAGE      = src/django_deprecated_field
BASE  	     = $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

UV          = uv

V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

.PHONY: all
all: lint test ; @ ## Lint and test project
	$Q

$(UV): ; $(info $(M) checking UV…)
	$Q

$(BASE): | $(UV) ; $(info $(M) checking PROJECT…)
	$Q

.PHONY: fix
fix: fix-ruff-lint fix-ruff-format | $(BASE) ; @ ## Run all fixers
	$Q

.PHONY: lint-backend
lint-backend: lint-ruff-lint lint-ruff-format lint-mypy | $(BASE) ; @ ## Run all backend linters
	$Q

.PHONY: lint
lint: lint-backend | $(BASE) ; @ ## Lint project
	$Q

.PHONY: test-backend
test-backend: test-pytest | $(BASE) ; @ ## Run pytest
	$Q

.PHONY: test
test: test-backend | $(BASE) ; @ ## Run tests
	$Q

# Tests
.PHONY: test-pytest
test-pytest: .venv | $(BASE) ; $(info $(M) running backend tests…) @ ## Run pytest
	$Q cd $(BASE) && PYTHONHASHSEED=0 $(UV) run pytest --numprocesses 3

.PHONY: test-pytest-coverage
test-pytest-coverage: .venv | $(BASE) ; $(info $(M) running tests with coverage…) @ ## Run pytest with coverage
	$Q cd $(BASE) && PYTHONHASHSEED=0 $(UV) run pytest \
        --numprocesses 8 \
		--cov \
		--cov-report=html \
		--cov-report=xml:coverage/pytest-cobertura.xml \
		--cov-report=term

# Linters

.PHONY: lint-ruff-lint
lint-ruff-lint: .venv | $(BASE) ; $(info $(M) running ruff…) @ ## Run ruff linter
	$Q cd $(BASE) && $(UV) run ruff check $(PACKAGE) tests

.PHONY: lint-ruff-format
lint-ruff-format: .venv | $(BASE) ; $(info $(M) running ruff…) @ ## Run ruff linter
	$Q cd $(BASE) && $(UV) run ruff format $(PACKAGE) tests --check

.PHONY: lint-mypy
lint-mypy: .venv | $(BASE) ; $(info $(M) running mypy…) @ ## Run mypy linter
	$Q cd $(BASE) && $(UV) run mypy --show-error-codes --show-column-numbers $(PACKAGE) tests

# Fixers

.PHONY: fix-ruff-lint
fix-ruff-lint: .venv | $(BASE) ; $(info $(M) running ruff…) @ ## Run ruff fixer
	$Q cd $(BASE) && $(UV) run ruff check $(PACKAGE) tests --fix

.PHONY: fix-ruff-format
fix-ruff-format: .venv | $(BASE) ; $(info $(M) running ruff…) @ ## Run ruff fixer
	$Q cd $(BASE) && $(UV) run ruff format $(PACKAGE) tests

# Dependency management

.venv: pyproject.toml | $(BASE) ; $(info $(M) retrieving dependencies…) @ ## Install python dependencies
	$Q cd $(BASE) && $(UV) venv
	$Q cd $(BASE) && $(UV) sync --dev
	@touch $@

# Misc

.PHONY: clean
clean: ; $(info $(M) cleaning…) @ ## Cleanup caches and virtual environment
	@rm -rf .eggs *.egg-info .venv test-reports
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +

.PHONY: help
help: ## This help message
	@grep -E '^[ a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' | sort
