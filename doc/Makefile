# Makefile for Sphinx documentation
#

SPHINXBUILD = sphinx-build
BUILDDIR    = _build
SPHINXOPTS  = -d $(BUILDDIR)/doctrees .
INSTALLDIR  = ../web/templates/doc

.PHONY: all html clean html install

all: html

html:
	$(SPHINXBUILD) -b html $(SPHINXOPTS) $(BUILDDIR)/html

clean:
	-rm -rf $(BUILDDIR)/*

install: html
	cp -pr  $(BUILDDIR)/html/* $(INSTALLDIR)/.
