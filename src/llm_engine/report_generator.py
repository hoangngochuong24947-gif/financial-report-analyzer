"""
====================================================================
模块名称：report_generator.py
模块功能：AI 分析报告生成器 — 串联所有分析模块，发送给 LLM，返回结构化报告

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 类/函数                      │ 方法                        │ 说明                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ ReportGenerator              │ generate_report()           │ 生成完整 AI 分析报告     │
│                              │ _collect_metrics()          │ 收集所有财务指标         │
│                              │ _build_prompt()             │ 组装分析 Prompt          │
│                              │ _parse_response()           │ 解析 LLM 回复           │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 调用 data_fetcher/akshare_client.py 获取原始数据
→ 调用 analyzer/ 各模块计算指标
→ 调用 llm_engine/llm_client.py 发送 Prompt
→ 返回 models/analysis_result.py 的 AnalysisReport
→ 被 api/routes_report.py 调用
====================================================================
"""

import re
from typing import Dict, Any, Optional

from src.analyzer.ratio_calculator import calc_profitability, calc_solvency, calc_efficiency
from src.analyzer.dupont_analyzer import analyze as dupont_analyze
from src.analyzer.cashflow_analyzer import analyze as cashflow_analyze
from src.analyzer.trend_analyzer import calc_yoy
from src.crawler.interfaces import FinancialDataGateway, FinancialSnapshot
from src.crawler.service import CrawlerService
from src.models.analysis_result import AnalysisReport
from src.storage.workspace_repository import ArchiveWorkspace
from src.api.workspace_service import WorkspaceService
from src.analyzer.metric_engine import WorkspaceMetricEngine
from src.llm_engine.context_builder import PromptContextBuilder
from src.llm_engine.llm_client import get_llm_client
from src.llm_engine.prompt_templates import (
    SYSTEM_PROMPT,
    COMPREHENSIVE_ANALYSIS_TEMPLATE,
    format_metrics_for_prompt,
)
from src.utils.logger import logger


class ReportGenerator:
    """
    AI 分析报告生成器

    工作流程：
    1. 通过 AKShareClient 获取三大报表
    2. 调用各 analyzer 模块计算所有指标
    3. 将指标格式化为 Prompt 文本
    4. 发送给 DeepSeek LLM 进行分析
    5. 解析 LLM 回复，填充 AnalysisReport 模型
    """

    def __init__(self, client: Optional[FinancialDataGateway] = None):
        """
        Args:
            client: AKShare 客户端实例（可选，默认新建）
        """
        self._client = client or CrawlerService()

    def generate_report(self, stock_code: str, stock_name: str = "") -> AnalysisReport:
        """
        生成完整的 AI 财务分析报告

        Args:
            stock_code: 股票代码（如 "600519"）
            stock_name: 股票名称（如 "贵州茅台"，可留空）

        Returns:
            AnalysisReport: 结构化分析报告

        Raises:
            RuntimeError: 数据获取失败或 LLM 调用失败

        Examples:
            >>> generator = ReportGenerator()
            >>> report = generator.generate_report("600519", "贵州茅台")
            >>> print(report.executive_summary)
        """
        logger.info(f"Generating AI report for {stock_code} ({stock_name})...")

        # Step 1: 组装 archive-first 上下文
        context = self._build_ai_context(stock_code, stock_name)

        # Step 2: 调用 LLM
        llm_client = get_llm_client()
        raw_response = llm_client.analyze(prompt=context.context_text, system_prompt=context.system_prompt)

        # Step 3: 解析回复并构建 AnalysisReport
        report = self._parse_response(
            raw_response=raw_response,
            stock_code=stock_code,
            stock_name=stock_name or stock_code,
            report_date=context.report_date,
        )

        logger.info(f"AI report generated for {stock_code}: {len(raw_response)} chars")
        return report

    def _build_ai_context(self, stock_code: str, stock_name: str):
        """
        Construct an archive-first AI context bundle.
        """
        try:
            workspace = WorkspaceService().get_workspace(stock_code)
        except Exception:
            workspace = ArchiveWorkspace(
                stock_code=stock_code,
                stock_name=stock_name or stock_code,
                market="ab",
                snapshot=self._build_live_snapshot(stock_code),
                archives=[],
                latest_report_date=None,
            )

        bundle = WorkspaceMetricEngine().build_bundle(snapshot=workspace.snapshot, stock_name=workspace.stock_name)
        return PromptContextBuilder().build(workspace=workspace, metric_bundle=bundle, profile_key="archive_review")

    def _build_live_snapshot(self, stock_code: str):
        """Fallback snapshot builder for legacy live-provider paths."""
        balance_sheets = self._client.fetch_balance_sheet(stock_code)
        income_statements = self._client.fetch_income_statement(stock_code)
        cashflow_statements = self._client.fetch_cashflow_statement(stock_code)

        if not balance_sheets or not income_statements:
            raise RuntimeError(f"无法获取 {stock_code} 的财务数据，请检查股票代码是否正确。")

        return FinancialSnapshot(
            stock_code=stock_code,
            balance_sheets=balance_sheets,
            income_statements=income_statements,
            cashflow_statements=cashflow_statements,
        )

    def _collect_metrics(self, stock_code: str) -> Dict[str, Any]:
        """
        收集所有财务指标数据

        Args:
            stock_code: 股票代码

        Returns:
            dict: 包含所有分析维度数据的字典

        内部调用：
        - AKShareClient.fetch_balance_sheet()
        - AKShareClient.fetch_income_statement()
        - AKShareClient.fetch_cashflow_statement()
        - calc_profitability(), calc_solvency(), calc_efficiency()
        - DuPontAnalyzer.analyze(), CashFlowAnalyzer.analyze()
        """
        metrics = {}

        # 获取三大报表（取最新一期）
        balance_sheets = self._client.fetch_balance_sheet(stock_code)
        income_statements = self._client.fetch_income_statement(stock_code)
        cashflow_statements = self._client.fetch_cashflow_statement(stock_code)

        if not balance_sheets or not income_statements:
            logger.error(f"Cannot get statements for {stock_code}")
            return {}

        bs = balance_sheets[0]   # 最新一期
        is_ = income_statements[0]
        metrics["report_date"] = str(bs.report_date)

        # 盈利能力
        profitability = calc_profitability(bs, is_)
        metrics["profitability"] = {
            "净资产收益率 (ROE)": str(profitability.roe),
            "总资产收益率 (ROA)": str(profitability.roa),
            "销售净利率": str(profitability.net_profit_margin),
            "毛利率": str(profitability.gross_profit_margin),
        }

        # 偿债能力
        solvency = calc_solvency(bs)
        metrics["solvency"] = {
            "流动比率": str(solvency.current_ratio),
            "速动比率": str(solvency.quick_ratio),
            "资产负债率": str(solvency.debt_to_asset_ratio),
            "产权比率": str(solvency.debt_to_equity_ratio),
        }

        # 运营效率
        efficiency = calc_efficiency(bs, is_)
        metrics["efficiency"] = {
            "总资产周转率": str(efficiency.asset_turnover),
            "权益乘数": str(efficiency.equity_turnover),
        }

        # 杜邦分析
        dupont = dupont_analyze(bs, is_)
        metrics["dupont"] = {
            "ROE": str(dupont.roe),
            "净利率（拆解因子）": str(dupont.net_profit_margin),
            "资产周转率（拆解因子）": str(dupont.asset_turnover),
            "权益乘数（拆解因子）": str(dupont.equity_multiplier),
        }

        # 现金流分析
        if cashflow_statements:
            cf = cashflow_statements[0]
            cashflow = cashflow_analyze(cf, is_)
            metrics["cashflow"] = {
                "经营活动现金流量净额": str(cashflow.operating_cashflow),
                "自由现金流": str(cashflow.free_cash_flow),
                "现金利润比": str(cashflow.cash_to_profit_ratio),
                "经营现金流覆盖率": str(cashflow.operating_cash_coverage),
            }
        else:
            metrics["cashflow"] = {"数据": "暂无现金流数据"}

        # 趋势分析（如果有多期数据）
        if len(income_statements) >= 2:
            trend = calc_yoy(
                current=is_.net_income,
                previous=income_statements[1].net_income,
            )
            metrics["trend"] = {
                "净利润同比增长率": str(trend),
                "当期净利润": str(is_.net_income),
                "上期净利润": str(income_statements[1].net_income),
            }
        else:
            metrics["trend"] = {"数据": "仅有单期数据，无法计算趋势"}

        return metrics

    def _build_prompt(
        self,
        stock_code: str,
        stock_name: str,
        report_date: str,
        metrics: Dict[str, Any],
    ) -> str:
        """
        组装综合分析 Prompt

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            report_date: 报告期
            metrics: 所有指标数据

        Returns:
            str: 渲染后的 Prompt 文本
        """
        prompt = COMPREHENSIVE_ANALYSIS_TEMPLATE.format(
            stock_code=stock_code,
            stock_name=stock_name or stock_code,
            report_date=report_date,
            profitability_data=format_metrics_for_prompt(metrics.get("profitability", {})),
            solvency_data=format_metrics_for_prompt(metrics.get("solvency", {})),
            efficiency_data=format_metrics_for_prompt(metrics.get("efficiency", {})),
            cashflow_data=format_metrics_for_prompt(metrics.get("cashflow", {})),
            dupont_data=format_metrics_for_prompt(metrics.get("dupont", {})),
            trend_data=format_metrics_for_prompt(metrics.get("trend", {})),
        )
        return prompt

    def _parse_response(
        self,
        raw_response: str,
        stock_code: str,
        stock_name: str,
        report_date: str,
    ) -> AnalysisReport:
        """
        解析 LLM 回复，提取各维度分析内容，构建 AnalysisReport

        Args:
            raw_response: LLM 原始回复文本
            stock_code: 股票代码
            stock_name: 股票名称
            report_date: 报告期

        Returns:
            AnalysisReport: 结构化分析报告
        """
        # 按标题拆分各段
        sections = self._split_sections(raw_response)

        # 提取各维度分析
        profitability_text = sections.get("盈利能力分析", "")
        solvency_text = sections.get("偿债能力分析", "")
        efficiency_text = sections.get("运营效率分析", "")
        cashflow_text = sections.get("现金流分析", "")
        trend_text = sections.get("趋势", "") or sections.get("杜邦分析", "")

        # 提取综合结论
        conclusion = sections.get("综合结论", "") or sections.get("综合评估", "")

        # 从完整回复中提取优势、劣势、建议
        # 注意：不能只从 conclusion 中提取，因为 _split_sections 会在 ### 处截断
        strengths = self._extract_list(raw_response, "优势")
        weaknesses = self._extract_list(raw_response, "劣势") or self._extract_list(raw_response, "风险")
        recommendations = self._extract_list(raw_response, "建议")

        # 如果无法精确拆分，使用整段回复
        if not profitability_text:
            profitability_text = raw_response[:500]

        # 生成执行摘要（取前 300 字符或第一段）
        executive_summary = self._generate_summary(raw_response)

        return AnalysisReport(
            stock_code=stock_code,
            stock_name=stock_name,
            report_date=report_date,
            executive_summary=executive_summary,
            profitability_analysis=profitability_text or "数据不足，无法分析",
            solvency_analysis=solvency_text or "数据不足，无法分析",
            efficiency_analysis=efficiency_text or "数据不足，无法分析",
            cashflow_analysis=cashflow_text or "数据不足，无法分析",
            trend_analysis=trend_text or "数据不足，无法分析",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            risk_warnings=self._extract_list(raw_response, "风险提示"),
        )

    @staticmethod
    def _split_sections(text: str) -> Dict[str, str]:
        """
        按标题拆分 LLM 回复中的各段内容

        使用 Markdown 标题（## 或 ###）作为分隔符。

        Args:
            text: LLM 原始回复

        Returns:
            dict: {标题关键词: 段落内容}
        """
        sections = {}
        # 匹配 ## 或 ### 标题
        pattern = r"#{2,3}\s*\d*\.?\s*(.*?)(?:\n|$)"
        matches = list(re.finditer(pattern, text))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            # 用关键词匹配存储
            for keyword in ["盈利能力", "偿债能力", "运营效率", "现金流",
                            "杜邦", "趋势", "风险", "综合结论", "综合评估"]:
                if keyword in title:
                    sections[keyword.replace("分析", "") + "分析" if "分析" not in keyword else keyword] = content
                    break
            else:
                sections[title] = content

        return sections

    @staticmethod
    def _extract_list(text: str, keyword: str) -> list:
        """
        从文本中提取以关键词开头的列表项

        Args:
            text: 源文本
            keyword: 关键词（如 "优势"、"劣势"）

        Returns:
            list: 提取到的列表项
        """
        items = []
        # 找到关键词所在段落
        lines = text.split("\n")
        in_section = False

        for line in lines:
            stripped = line.strip()
            if keyword in stripped and (":" in stripped or "：" in stripped or "#" in stripped):
                in_section = True
                continue
            if in_section:
                # 遇到下一个标题或空行，结束
                if stripped.startswith("#") or (not stripped and items):
                    break
                # 提取列表项
                if stripped.startswith(("-", "•", "·", "*")) or re.match(r"^\d+[.、]", stripped):
                    item = re.sub(r"^[-•·*\d.、]+\s*", "", stripped).strip()
                    if item:
                        items.append(item)

        return items

    @staticmethod
    def _generate_summary(text: str) -> str:
        """
        从 LLM 回复中提取执行摘要

        取第一段非标题文本，最多 300 字符。

        Args:
            text: LLM 原始回复

        Returns:
            str: 执行摘要
        """
        lines = text.split("\n")
        summary_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if summary_lines:
                    break
                continue
            if stripped.startswith("#"):
                if summary_lines:
                    break
                continue
            summary_lines.append(stripped)

        summary = " ".join(summary_lines)
        if len(summary) > 300:
            summary = summary[:297] + "..."
        return summary or "分析报告已生成，请查看各维度详情。"


"""
====================================================================
【使用示例】

from src.llm_engine.report_generator import ReportGenerator

generator = ReportGenerator()

# 生成 AI 分析报告
report = generator.generate_report("600519", "贵州茅台")

print(f"摘要: {report.executive_summary}")
print(f"优势: {report.strengths}")
print(f"劣势: {report.weaknesses}")
print(f"建议: {report.recommendations}")

====================================================================
"""
