SKILL_NAME := japan-real-estate-data-retriever
SKILL_SOURCE := $(CURDIR)/skills/$(SKILL_NAME)
SKILL_HOME ?= $(HOME)/.agents/skills

.PHONY: sync install-local install-skill-dev install-codex-skill-dev install-hermes-dev test smoke smoke-skill

sync:
	uv sync

install-local:
	uv tool install --editable . --force

install-skill-dev:
	mkdir -p "$(SKILL_HOME)"
	if [ -e "$(SKILL_HOME)/$(SKILL_NAME)" ] && [ ! -L "$(SKILL_HOME)/$(SKILL_NAME)" ]; then \
		echo "error: $(SKILL_HOME)/$(SKILL_NAME) exists and is not a symlink" >&2; \
		exit 1; \
	fi
	rm -f "$(SKILL_HOME)/$(SKILL_NAME)"
	ln -s "$(SKILL_SOURCE)" "$(SKILL_HOME)/$(SKILL_NAME)"
	test -f "$(SKILL_HOME)/$(SKILL_NAME)/SKILL.md"

install-codex-skill-dev:
	$(MAKE) install-skill-dev SKILL_HOME="$(HOME)/.codex/skills"

install-hermes-dev: install-local install-skill-dev smoke

test:
	uv run python -m unittest discover -s tests

smoke:
	command -v jreretrieve
	cd /tmp && jreretrieve --help
	cd /tmp && jreretrieve --json doctor
	cd /tmp && jreretrieve --json sources list

smoke-skill:
	test -L "$(SKILL_HOME)/$(SKILL_NAME)" -o -d "$(SKILL_HOME)/$(SKILL_NAME)"
	test -f "$(SKILL_HOME)/$(SKILL_NAME)/SKILL.md"
