# This Docker image is based on Debian Bullseye instead of Alpine
# because the latter uses musl and does not support locales.

FROM python:3.9-slim-bullseye as build
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
    mkdir -p "$workdir"
WORKDIR "$workdir"
COPY --chown=bot:bot entrypoint.sh *.py *.yml ./
# Docker (up to version 20.10) cannot copy multiple directories in a single layer (`COPY` command), its content only.
# See https://stackoverflow.com/questions/26504846/copy-directory-to-another-directory-using-add-command.
# So copying directories one by one.
COPY --from=build --chown=bot:bot /venv venv
COPY --from=build --chown=bot:bot /locales locales
USER bot
RUN sed "/^VIRTUAL_ENV=/s:/:$PWD/:" -i venv/bin/activate && chmod +x entrypoint.sh
ENV PATH="$workdir:$PATH" LANG="ru_RU.UTF-8" LC_MESSAGES="en_US.UTF-8"
ENTRYPOINT ["entrypoint.sh"]
CMD ["python", "fossnewsbot.py"]
