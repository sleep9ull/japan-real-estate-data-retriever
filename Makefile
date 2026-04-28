.PHONY: install-local test smoke

install-local:
	uv tool install --editable . --force

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

smoke:
	jreretrieve --help
	jreretrieve --json doctor
	jreretrieve --json sources list
