from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "CryptoSight"
    api_prefix: str = "/api"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./cryptosight.db",
    )
    okx_base_url: str = os.getenv("OKX_BASE_URL", "https://www.okx.com")
    okx_instrument_id: str = os.getenv("OKX_INSTRUMENT_ID", "BTC-USDT")
    okx_bar: str = os.getenv("OKX_BAR", "1D")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_search_query: str = os.getenv("X_SEARCH_QUERY", '(bitcoin OR btc OR crypto) lang:en -is:retweet')
    x_search_limit: int = int(os.getenv("X_SEARCH_LIMIT", "25"))
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "CryptoSight/0.1 by relphclaw")
    reddit_search_query: str = os.getenv("REDDIT_SEARCH_QUERY", "bitcoin OR btc OR crypto")
    reddit_search_subreddit: str = os.getenv("REDDIT_SEARCH_SUBREDDIT", "CryptoCurrency")
    reddit_search_limit: int = int(os.getenv("REDDIT_SEARCH_LIMIT", "25"))
    news_search_query: str = os.getenv("NEWS_SEARCH_QUERY", "(bitcoin OR btc OR crypto) language:english")
    news_search_limit: int = int(os.getenv("NEWS_SEARCH_LIMIT", "25"))
    live_data_enabled: bool = os.getenv("LIVE_DATA_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    cors_origins: list[str] = ["*"]
    default_history_limit: int = 365


@lru_cache
def get_settings() -> Settings:
    return Settings()
