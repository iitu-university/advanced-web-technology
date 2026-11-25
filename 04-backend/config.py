from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", hide_input_in_errors=True)

    database_url: str
    secret_key: str = Field(min_length=32, repr=False)
    access_token_minutes: int = Field(default=15, gt=0)
    sql_echo: bool = False
    graphql_introspection: bool = True


settings = Settings()
