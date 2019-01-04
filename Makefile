.PHONY: all test docs

PYTHON := python
DOCS_DIR := doc
RST_SRCDIR := $(DOCS_DIR)/source
BUILD := build

all:
	$(PYTHON) setup.py build_exe

docs:
	sphinx-apidoc -o $(RST_SRCDIR) . -f
	make clean html -C $(DOCS_DIR)

test:
	@py -2 -m pytest -v

clean:
	[ -d $(BUILD) ] && rm -rf $(BUILD)
