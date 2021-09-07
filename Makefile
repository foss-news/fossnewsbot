SHELL := /bin/bash

copyright := PermLUG
email := Vasiliy Polyakov <fossnews@invasy.dev>
pkgname := fossnewsbot
pkgver := 0.1.0
pkgdir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
localesdir := $(pkgdir)locales/
domain := $(pkgname)
languages := en ru

po = $(localesdir)$1/LC_MESSAGES/$(domain).po

src := $(pkgname).py
pot := $(localesdir)$(domain).pot
pos := $(foreach lang,$(languages),$(call po,$(lang)))
mos := $(pos:.po=.mo)

.PHONY: all locales
all: locales
locales: $(mos)

%.mo: %.po
	@msgfmt --output-file=$@ $<

ifdef UPDATE_PO_FROM_POT
define rule_po
$(call po,$1): $(pot)
	@mkdir -p $$(dir $$@) && \
	msginit --input=$$< --no-translator --locale=$1 --output-file=$$@
endef

.PHONY: po
po: $(pos)

$(foreach lang,$(languages),$(eval $(call rule_po,$(lang))))
endif

ifdef UPDATE_POT_FROM_SOURCE
.PHONY: pot
pot: $(pot)

$(pot): $(src) | $(localesdir)
	@xgettext --package-name="$(pkgname)" --package-version="$(pkgver)" \
		--copyright-holder="$(copyright)" --msgid-bugs-address="$(email)" \
		--from-code=utf-8 --default-domain=$(domain) --add-comments --output=$@ $^

$(localesdir):
	@mkdir -p $@
endif
