PYTHON := python

CAPTCHA_IDENTIFIER_URL := https://github.com/scwang98/Captcha_Identifier/archive/refs/heads/main.tar.gz

.DEFAULT_GOAL := help

define DL
	curl -L $(1) -o $(2)
endef

define UNZIP
	mkdir -p $(2) && tar xf $(1) --strip-components 1 -C $(2)
endef

help:
	@echo "Usage: "
	@echo "  make prepare               Download and patch dependencies"
	@echo "  make book                  Run booking script"
	@echo "  make clean                 Remove downloaded dependencies"

deps:
	@mkdir -p deps

deps/Captcha_Identifier.tar.gz: deps
	@$(call DL, $(CAPTCHA_IDENTIFIER_URL), $@)

Captcha_Identifier: deps/Captcha_Identifier.tar.gz
	rm -rf Captcha_Identifier && mkdir Captcha_Identifier
	@$(call UNZIP, $<, Captcha_Identifier)
	git apply --directory Captcha_Identifier ./patches/Captcha_Identifier-001-fix-integration.patch

prepare: Captcha_Identifier

check_tesseract:
	@which tesseract > /dev/null || (echo "Tesseract is not installed" && exit 1)

book: check_tesseract
	$(PYTHON) main.py

clean:
	rm -rf Captcha_Identifier deps __pycache__
