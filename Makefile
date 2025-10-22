.PHONY: help install test build clean bump-patch bump-minor bump-major release

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies including dev dependencies
	uv sync --all-extras

test:  ## Run tests
	uv run --with pytest python -m pytest tests/ -v

build:  ## Build the package
	uv build

clean:  ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

bump-patch:  ## Bump patch version (1.2.3 -> 1.2.4)
	uv run --with bump-my-version bump-my-version bump patch

bump-minor:  ## Bump minor version (1.2.3 -> 1.3.0)
	uv run --with bump-my-version bump-my-version bump minor

bump-major:  ## Bump major version (1.2.3 -> 2.0.0)
	uv run --with bump-my-version bump-my-version bump major

show-version:  ## Show current version
	@uv run --with bump-my-version bump-my-version show current_version

release-patch: bump-patch  ## Create a patch release (bump version, commit, tag, and push)
	git push && git push --tags

release-minor: bump-minor  ## Create a minor release (bump version, commit, tag, and push)
	git push && git push --tags

release-major: bump-major  ## Create a major release (bump version, commit, tag, and push)
	git push && git push --tags
