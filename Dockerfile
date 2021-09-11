# Dockerfile for FOSS News Telegram Bot.
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

# This Docker image is based on Debian Bullseye instead of Alpine
# because the latter uses musl and therefore does not support locales.
FROM python:3.9-slim-bullseye as build

# Copy source files for venv and locales got the image
COPY requirements.txt /
COPY locales /locales

# Create Python virtual environment, install dependences, compile translations.
RUN set -eu;\
    apt-get update -qq; apt-get install -qqy gcc gettext; rm -rf /var/lib/apt/lists/*;\
    python -m venv /venv; . /venv/bin/activate; pip install --upgrade pip; pip install -r /requirements.txt;\
    for po in /locales/*/LC_MESSAGES/*.po; do msgfmt --output-file="${po%.po}.mo" "$po"; rm "$po"; done


FROM python:3.9-slim-bullseye as fossnewsbot
ARG lang="ru_RU.UTF-8"
ARG tz="Asia/Yekaterinburg"
ARG workdir="/srv/fossnewsbot"

# Install and setup locales and timezone; create user `bot` and working directory.
RUN set -eu;\
    apt-get update -qq; apt-get install -qqy locales; rm -rf /var/lib/apt/lists/*;\
    echo "en_US.UTF-8 UTF-8\n${lang} ${lang#*.}" >/etc/locale.gen; locale-gen; echo "LANG=$lang" >/etc/default/locale;\
    echo "en_US\ten_US.UTF-8\nen\ten_US.UTF-8\n${lang%.*}\t${lang}\n${lang%_*}\t${lang}" >/etc/locale.alias;\
    echo "$tz" >/etc/timezone; ln -sf "/usr/share/zoneinfo/$tz" /etc/localtime;\
    useradd --create-home --comment='FOSS News Bot' --user-group bot; yes bot | passwd bot;\
    mkdir -p "$workdir" \

# Copy bot code and configuration to the image
WORKDIR "$workdir"
COPY --chown=bot:bot cache.py config.py config.yml .secrets.yml entrypoint.sh ./
# Docker (up to version 20.10) cannot copy multiple directories in a single layer (`COPY` command), its content only.
# See https://stackoverflow.com/questions/26504846/copy-directory-to-another-directory-using-add-command.
# So copying directories one by one.
COPY --chown=bot:bot fossnewsbot fossnewsbot
COPY --from=build --chown=bot:bot /venv venv
COPY --from=build --chown=bot:bot /locales locales

# Change user AFTER all chowns
USER bot
# Correct venv directory in the activation script and make entrypoint script executable
RUN sed "/^VIRTUAL_ENV=/s:/:$PWD/:" -i venv/bin/activate && chmod +x entrypoint.sh

ENV PATH="$workdir:$PATH" LANG="ru_RU.UTF-8" LC_MESSAGES="en_US.UTF-8"
ENTRYPOINT ["entrypoint.sh"]
CMD ["python", "-m", "fossnewsbot"]
