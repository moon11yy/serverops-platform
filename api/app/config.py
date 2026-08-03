from dataclasses import dataclass
import os
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Settings:
    database_url: str
    mongo_uri: str
    mongo_database: str
    log_level: str


def load_settings() -> Settings:
    postgres_user = quote_plus(os.getenv("POSTGRES_USER", "serverops"))
    postgres_password = quote_plus(os.getenv("POSTGRES_PASSWORD", "serverops"))
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB", "serverops")

    mongo_user = quote_plus(os.getenv("MONGO_ROOT_USERNAME", "serverops"))
    mongo_password = quote_plus(os.getenv("MONGO_ROOT_PASSWORD", "serverops"))
    mongo_host = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")

    database_url = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg://{postgres_user}:{postgres_password}@"
        f"{postgres_host}:{postgres_port}/{postgres_db}",
    )
    mongo_uri = os.getenv(
        "MONGO_URI",
        f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/?authSource=admin",
    )

    return Settings(
        database_url=database_url,
        mongo_uri=mongo_uri,
        mongo_database=os.getenv("MONGO_DATABASE", "serverops"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


settings = load_settings()
