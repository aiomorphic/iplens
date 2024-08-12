.PHONY: pre-commit
pre-commit:
	@echo "Starting pre-commit checks..."
	@pre-commit run --all-files