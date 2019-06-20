.PHONY: all test docs

PYTHON := python
DOCS_DIR := doc
RST_SRCDIR := $(DOCS_DIR)/source
PYTHON_SRCDIR := text_game_maker
BUILD := build
AUTODOC_EXCLUDE_DIRS := text_game_maker/example.py text_game_maker/runner.py\
	text_game_maker/example-map/* text_game_maker/slackbot_runner.py

all:
	$(PYTHON) cxfreeze-setup.py build_exe

autodoc:
	sphinx-apidoc -f -E -M -o $(RST_SRCDIR) $(PYTHON_SRCDIR) $(AUTODOC_EXCLUDE_DIRS)

docs: autodoc
	make clean html -C $(DOCS_DIR)

test:
	@py -2 -m pytest -v

clean:
	[ -d $(BUILD) ] && rm -rf $(BUILD)
