.PHONY: all test docs

PYTHON := python
DOCS_DIR := doc
RST_SRCDIR := $(DOCS_DIR)/source
PYTHON_SRCDIR := text_game_maker
BUILD := build

all:
	$(PYTHON) setup.py build_exe

autodoc:
	sphinx-apidoc -E -M -o $(RST_SRCDIR) $(PYTHON_SRCDIR) -f

docs: autodoc
	make clean html -C $(DOCS_DIR)

test:
	@py -2 -m pytest -v

clean:
	[ -d $(BUILD) ] && rm -rf $(BUILD)
