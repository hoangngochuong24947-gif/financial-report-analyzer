"""
====================================================================
模块名称：dependencies.py
模块功能：FastAPI 依赖注入

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ get_akshare_client()         │ 无                          │ AKShareClient            │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被所有 API 路由使用（依赖注入）
====================================================================
"""

from src.data_fetcher.akshare_client import AKShareClient


def get_akshare_client() -> AKShareClient:
    """
    获取 AKShareClient 实例（依赖注入）

    Returns:
        AKShareClient: AKShare 客户端实例
    """
    return AKShareClient()


"""
====================================================================
【使用示例】

from fastapi import Depends
from src.api.dependencies import get_akshare_client

@app.get("/stocks/{code}")
async def get_stock(
    code: str,
    client: AKShareClient = Depends(get_akshare_client)
):
    data = client.fetch_balance_sheet(code)
    return data

====================================================================
"""
