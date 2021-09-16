# Makefile for FOSS News Telegram Bot.
#
# Copyright (C) 2021 PermLUG
#
# This file is part of fossnewsbot, FOSS News Telegram Bot.
#
# fossnewsbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# fossnewsbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

SHELL := /bin/bash

copyright := PermLUG
email := Vasiliy Polyakov <fossnews@invasy.dev>
pkgname := fossnewsbot
pkgver := 0.1.0
pkgdir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
localesdir := $(pkgdir)locales/
domain := $(pkgname)
languages := en ru

tag := $(pkgname):$(pkgver)

po = $(localesdir)$1/LC_MESSAGES/$(domain).po

src := $(pkgname).py
pot := $(localesdir)$(domain).pot
pos := $(foreach lang,$(languages),$(call po,$(lang)))
mos := $(pos:.po=.mo)

.PHONY: all image locales
all: locales

image: Dockerfile
	@docker build --tag="$(tag)" --tag="$(pkgname):latest" .

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
