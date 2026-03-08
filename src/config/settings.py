"""
====================================================================
模块名称：settings.py
模块功能：应用配置管理（使用 pydantic Settings）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 类/函数                      │ 属性/方法                   │ 说明                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ Settings                     │ mysql_host, mysql_port...   │ 全局配置单例             │
│                              │ redis_host, redis_port...   │                          │
│                              │ deepseek_api_key...         │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 在 main.py 启动时加载
→ 所有模块通过 from src.config.settings import settings 使用
====================================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类（自动从环境变量和 .env 文件加载）
    """

    # MySQL 配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "financial_analyzer"

    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # LLM 配置
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 应用配置
    log_level: str = "INFO"
    cache_ttl: int = 3600  # 缓存过期时间（秒）

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # 数据库连接池配置
    db_pool_size: int = 5
    db_max_overflow: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def mysql_url(self) -> str:
        """
        生成 MySQL 连接 URL

        Returns:
            str: SQLAlchemy 格式的连接字符串
        """
        return f"mysql+mysqlconnector://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"

    @property
    def redis_url(self) -> str:
        """
        生成 Redis 连接 URL

        Returns:
            str: Redis 连接字符串
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# 全局配置实例（单例）
settings = Settings()


"""
====================================================================
【使用示例】

from src.config.settings import settings

# 1. 访问配置
db_url = settings.mysql_url
api_key = settings.deepseek_api_key

# 2. 在 FastAPI 中使用
@app.on_event("startup")
async def startup():
    logger.info(f"Starting API on {settings.api_host}:{settings.api_port}")

# 3. 在数据库连接中使用
engine = create_engine(settings.mysql_url)

====================================================================
"""
