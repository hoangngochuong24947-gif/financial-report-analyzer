"""
====================================================================
模块名称：main.py
模块功能：FastAPI 应用入口

【应用配置】
- 注册所有路由
- 配置 CORS
- 初始化日志系统
- 启动事件处理

【数据流向】
→ 应用启动入口
====================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.utils.logger import setup_logger, logger
from src.api import routes_stock, routes_analysis, routes_report

# 初始化日志
setup_logger(log_level=settings.log_level)

# 创建 FastAPI 应用
app = FastAPI(
    title="财务报表分析系统 / Financial Report Analyzer",
    description="A股上市公司财务报表自动分析系统",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(routes_stock.router)
app.include_router(routes_analysis.router)
app.include_router(routes_report.router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 60)
    logger.info("Financial Report Analyzer Starting...")
    logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info(f"MySQL: {settings.mysql_host}:{settings.mysql_port}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Financial Report Analyzer Shutting Down...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "财务报表分析系统 API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "financial-report-analyzer"
    }


"""
====================================================================
【启动命令】

# 开发模式（自动重载）
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# 使用 Poetry
poetry run uvicorn src.main:app --reload

====================================================================
"""
