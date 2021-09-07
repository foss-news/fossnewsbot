#!/bin/sh
# vim: set ft=sh et sw=2 ts=2:
# shellcheck disable=SC2164
cd "${0%/*}"
export LANGUAGE="${LANG%.*}:en_US"
. venv/bin/activate
"$@"
