"""
====================================================================
模块名称：llm_client.py
模块功能：LLM 客户端，封装 LangChain + DeepSeek API 调用

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 类/函数                      │ 方法                        │ 说明                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ LLMClient                    │ analyze(prompt)             │ 发送 Prompt 并返回文本   │
│                              │ analyze_structured(prompt)  │ 返回结构化 JSON          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 llm_engine/report_generator.py 调用
→ 被 api/routes_report.py 间接使用
====================================================================
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config.settings import settings
from src.utils.logger import logger


class LLMClient:
    """
    LLM 客户端 — 使用 LangChain ChatOpenAI 兼容接口连接 DeepSeek

    DeepSeek API 完全兼容 OpenAI 格式，因此直接使用 ChatOpenAI 即可。
    """

    def __init__(self):
        """
        初始化 LLM 客户端

        从 settings 读取 DeepSeek 配置：
        - deepseek_api_key: API 密钥
        - deepseek_api_base: API 地址（https://api.deepseek.com）
        - deepseek_model: 模型名称（deepseek-chat）
        """
        if not settings.deepseek_api_key:
            logger.warning("DEEPSEEK_API_KEY is not set. LLM features will be unavailable.")

        self._llm = ChatOpenAI(
            model=settings.deepseek_model,
            openai_api_key=settings.deepseek_api_key,
            openai_api_base=settings.deepseek_api_base,
            temperature=0.3,       # 财务分析需要稳定输出
            max_tokens=4096,
            request_timeout=120,   # 长文本分析可能耗时较长
        )
        logger.info(
            f"LLMClient initialized: model={settings.deepseek_model}, "
            f"base_url={settings.deepseek_api_base}"
        )

    def analyze(self, prompt: str, system_prompt: str = "") -> str:
        """
        发送 Prompt 并返回 LLM 文本

        Args:
            prompt: 用户 Prompt（包含财务数据和分析要求）
            system_prompt: 系统 Prompt（设定 LLM 角色和输出格式）

        Returns:
            str: LLM 生成的分析文本

        Raises:
            RuntimeError: API 调用失败时抛出

        Examples:
            >>> client = LLMClient()
            >>> result = client.analyze("分析贵州茅台2023年盈利能力")
        """
        if not settings.deepseek_api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY 未配置。请在 .env 文件中设置 DEEPSEEK_API_KEY。"
            )

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            logger.info(f"Sending prompt to LLM ({len(prompt)} chars)...")
            response = self._llm.invoke(messages)
            result = response.content

            logger.info(f"LLM response received ({len(result)} chars)")
            logger.debug(f"LLM response preview: {result[:200]}...")

            return result

        except Exception as e:
            logger.error(f"LLM API call failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"LLM 分析失败: {e}") from e


# 全局单例（延迟初始化）
_llm_client = None


def get_llm_client() -> LLMClient:
    """
    获取全局 LLMClient 单例

    Returns:
        LLMClient: 全局客户端实例
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


"""
====================================================================
【使用示例】

from src.llm_engine.llm_client import get_llm_client

client = get_llm_client()

# 1. 简单分析
result = client.analyze("请分析以下财务数据...")

# 2. 带系统提示的分析
result = client.analyze(
    prompt="ROE=15%, ROA=8%, 净利率=30%...",
    system_prompt="你是一名专业的财务分析师，请用中文回答。"
)

====================================================================
"""
