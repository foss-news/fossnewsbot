# FOSS News Bot

There are hundreds and hundreds of news collected every week for the FOSS News digest.

FOSS News Telegram Bot sends you those news one by one to filter and categorize.

[Take part in making the next digest on the go!](https://t.me/fossnewsbot "FOSS News Bot") 😃

## Run
### Development
```bash
docker-compose up -d fossnewsbot-dev
```

### Production
```bash
docker-compose up -d fossnewsbot
```

## Configuration
FOSS News Bot uses [Dynaconf](https://www.dynaconf.com/ "Dynaconf")
to handle configuration files and environment variables.

### Parameters
| Key                | Description                                      | Secret? | Type  | Default value                      |
|--------------------|--------------------------------------------------|:-------:|-------|------------------------------------|
| `log.level`        | Logging level                                    | No      | `str` | `"info"`                           |
| `fngs.endpoint`    | FOSS News Gathering Server API endpoint          | No      | `str` | `"https://fn.permlug.org/api/v1/"` |
| `fngs.username`    | Username for FOSS News Gathering Server API      | **Yes** | `str` |                                    |
| `fngs.password`    | Password for FOSS News Gathering Server API      | **Yes** | `str` |                                    |
| `bot.token`        | Authentication token for [Telegram Bot API][bot] | **Yes** | `str` |                                    |
| `cache.token.ttl`  | FNGS token time to live (in days)                | No      | `int` | `29`                               |
| `cache.attrs.ttl`  | News attributes time to live (in days)           | No      | `int` | `1`                                |
| `cache.users.size` | FNGS users cache size — number of cached users   | No      | `int` | `256`                              |
| `url.channel`      | URL of [PermLUG channel][channel] in Telegram    | No      | `str` | `"https://t.me/permlug"`           |
| `url.chat`         | URL of [PermLUG chat][chat] in Telegram          | No      | `str` | `"https://t.me/permlug_chat"`      |
| `localedir`        | Directory with locales (translations)            | No      | `str` | `"locales"`                        |
| `marker.date`      | Emoji marker for news date and time              | No      | `str` | `"🗓"`                              |
| `marker.lang`      | Emoji marker for news language                   | No      | `str` | `"🌏"`                              |
| `marker.category`  | Emoji marker for news category                   | No      | `str` | `"🗂"`                              |
| `marker.include`   | Emoji marker for news included in digest         | No      | `str` | `"✅"`                              |
| `marker.exclude`   | Emoji marker for news excluded from digest       | No      | `str` | `"⛔️"`                             |
| `marker.unknown`   | Emoji marker for skipped news                    | No      | `str` | `"🤷🏻‍♂️"`                            |
| `marker.main`      | Emoji marker for main news                       | No      | `str` | `"❗️"`                              |
| `marker.short`     | Emoji marker for short (title only) news         | No      | `str` | `"📃"`                              |
| `marker.error`     | Emoji marker for error message                   | No      | `str` | `"🤔"`                              |
| `keyboard.columns` | Number of columns in categories keyboard         | No      | `int` | `3`                                |

_Parameters with no default value must be set explicitly._

### Secrets
Sensitive data for bot (tokens, passwords etc.) must be stored in configuration file `.secrets.yml`
(see [Secrets](https://www.dynaconf.com/secrets/ "Secrets — Dynaconf Documentation")).
This file is excluded from Git (see [`.gitignore`](.gitignore)).

A value `<dict>.dynaconf_merge = true` must be defined for every dict in every environment
(see [Merging](https://www.dynaconf.com/merging/ "Merging — Dynaconf Documentation")).

See secrets file template in [`.secrets.yml.dist`](.secrets.yml.dist).

[bot]: https://core.telegram.org/bots/api "Telegram Bot API"
[channel]: https://t.me/permlug "PermLUG channel"
[chat]: https://t.me/permlug_chat "PermLUG chat"
