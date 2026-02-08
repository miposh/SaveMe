from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix=False,
    environments=True,
    env_switcher="ENV_FOR_DYNACONF",
    settings_files=[
        "config/settings.toml",
        "config/.secrets.toml",
    ],
    load_dotenv=True,
)
