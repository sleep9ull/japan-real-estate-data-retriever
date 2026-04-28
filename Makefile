.PHONY: sync install-local test smoke

sync:
	uv sync

install-local:
	uv tool install --editable . --force

test:
	uv run python -m unittest discover -s tests

smoke:
	command -v jreretrieve
	cd /tmp && jreretrieve --help
	cd /tmp && jreretrieve --json doctor
	cd /tmp && jreretrieve --json sources list
