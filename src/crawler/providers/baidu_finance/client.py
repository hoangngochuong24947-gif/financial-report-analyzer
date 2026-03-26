from __future__ import annotations

from typing import Any, Dict

from curl_cffi import requests

from src.config.settings import settings


class BaiduFinanceHTTPClient:
    """HTTP client for Baidu finance endpoints."""

    def __init__(self) -> None:
        self._headers = {
            "accept": "application/vnd.finance-web.v1+json, application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "origin": "https://gushitong.baidu.com",
            "referer": "https://gushitong.baidu.com/",
            "user-agent": settings.baidu_finance_user_agent,
        }

    def get_json(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.get(
            url,
            params=params,
            headers=self._headers,
            impersonate="chrome136",
            timeout=settings.baidu_finance_timeout,
        )
        response.raise_for_status()
        return response.json()
