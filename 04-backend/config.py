from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    sql_echo: bool = False
    graphql_introspection: bool = True


settings = Settings()
