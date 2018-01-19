.PHONY: test docs

DOCS_DIR := doc
RST_SRCDIR := $(DOCS_DIR)/source

docs:
	sphinx-apidoc -o $(RST_SRCDIR) . -f
	make clean html -C $(DOCS_DIR)

test:
	@py -2 -m pytest -v
