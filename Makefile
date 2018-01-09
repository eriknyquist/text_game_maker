DOCS_DIR := doc
RST_SRCDIR := $(DOCS_DIR)/source

docs:
	sphinx-apidoc -o $(RST_SRCDIR) . -f
	make clean html -C $(DOCS_DIR)
