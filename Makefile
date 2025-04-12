CAPTCHA_IDENTIFIER_URL := https://github.com/scwang98/Captcha_Identifier/archive/main.zip

.DEFAULT_GOAL := help

define DL
	curl -L $(1) -o $(2)
endef

define UNZIP
	unzip -q $(1) -d $(2)
endef

help:
	@echo "Usage: "
	@echo "  make prepare               Download and patch dependencies"
	@echo "  make clean                 Remove downloaded dependencies"

zips:
	@mkdir -p zips

zips/Captcha_Identifier.zip: zips
	@$(call DL, $(CAPTCHA_IDENTIFIER_URL), $@)

Captcha_Identifier: zips/Captcha_Identifier.zip
	rm -rf Captcha_Identifier && mkdir Captcha_Identifier
	@$(call UNZIP, $<, Captcha_Identifier)
	mv Captcha_Identifier/Captcha_Identifier-main/* Captcha_Identifier/
	mv Captcha_Identifier/Captcha_Identifier-main/.* Captcha_Identifier/
	rmdir Captcha_Identifier/Captcha_Identifier-main
	git apply --directory Captcha_Identifier ./patches/Captcha_Identifier-001-fix-integration.patch

prepare: Captcha_Identifier

clean:
	rm -rf Captcha_Identifier zips
