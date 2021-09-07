from dynaconf import Dynaconf

PREFIX = 'FOSSNEWSBOT'

config = Dynaconf(
    envvar_prefix=PREFIX,
    envvar=f'{PREFIX}_CONFIG',
    env_switcher=f'{PREFIX}_ENV',
    environments=True,
    settings_files=['config.yml', '.secrets.yml'],
)
