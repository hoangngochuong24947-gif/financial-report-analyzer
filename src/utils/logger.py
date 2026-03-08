"""
====================================================================
模块名称：logger.py
模块功能：Loguru 日志配置

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ setup_logger()               │ log_level: str              │ Logger                   │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 在 main.py 启动时调用一次
→ 所有模块通过 from src.utils.logger import logger 使用
====================================================================
"""

import sys
from pathlib import Path
from loguru import logger

# 移除默认的 handler
logger.remove()


def setup_logger(log_level: str = "INFO") -> logger:
    """
    配置 Loguru 日志系统

    Args:
        log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）

    Returns:
        Logger: 配置好的 logger 实例
    """
    # 创建 logs 目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 控制台输出（彩色，简洁格式）
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # 文件输出（详细格式，按日期轮转）
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
    )

    # 错误日志单独记录
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        encoding="utf-8",
    )

    logger.info(f"Logger initialized with level: {log_level}")
    return logger


# 默认初始化（可在 main.py 中重新配置）
setup_logger()


"""
====================================================================
【使用示例】

from src.utils.logger import logger

# 基本日志
logger.info("正在获取股票数据: {}", stock_code)
logger.warning("缓存未命中，从 AKShare 获取数据")
logger.error("数据库连接失败: {}", error)

# 异常日志（自动记录堆栈）
try:
    result = risky_operation()
except Exception as e:
    logger.exception("操作失败")

# 调试日志
logger.debug("原始数据: {}", raw_data)

====================================================================
"""
