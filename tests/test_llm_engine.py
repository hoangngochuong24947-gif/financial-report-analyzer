"""
====================================================================
模块名称：test_llm_engine.py
模块功能：LLM 引擎测试（Prompt 模板渲染、响应解析）

注意：使用 Mock 替代真实 LLM 调用，避免消耗 API 额度
====================================================================
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.llm_engine.prompt_templates import (
    SYSTEM_PROMPT,
    COMPREHENSIVE_ANALYSIS_TEMPLATE,
    format_metrics_for_prompt,
)
from src.llm_engine.report_generator import ReportGenerator


# ============================================================
# Prompt 模板测试
# ============================================================

class TestPromptTemplates:
    """Prompt 模板渲染测试"""

    def test_system_prompt_not_empty(self):
        """系统 Prompt 不为空"""
        assert len(SYSTEM_PROMPT) > 100
        assert "财务分析师" in SYSTEM_PROMPT

    def test_comprehensive_template_renders(self):
        """综合分析模板能正确渲染"""
        prompt = COMPREHENSIVE_ANALYSIS_TEMPLATE.format(
            stock_code="600519",
            stock_name="贵州茅台",
            report_date="2023-12-31",
            profitability_data="- ROE: 0.2500",
            solvency_data="- 流动比率: 3.50",
            efficiency_data="- 总资产周转率: 0.50",
            cashflow_data="- 经营现金流: 500亿",
            dupont_data="- ROE = 0.30 × 0.50 × 1.67",
            trend_data="- 净利润同比增长: 15%",
        )

        assert "600519" in prompt
        assert "贵州茅台" in prompt
        assert "ROE" in prompt
        assert "盈利能力分析" in prompt
        assert "偿债能力分析" in prompt
        assert "杜邦分析" in prompt

    def test_format_metrics(self):
        """指标格式化函数"""
        data = {"ROE": "0.1500", "ROA": "0.0800"}
        result = format_metrics_for_prompt(data)

        assert "- ROE: 0.1500" in result
        assert "- ROA: 0.0800" in result

    def test_format_metrics_empty(self):
        """空字典返回空字符串"""
        result = format_metrics_for_prompt({})
        assert result == ""


# ============================================================
# ReportGenerator 响应解析测试
# ============================================================

class TestReportGeneratorParsing:
    """测试 ReportGenerator 的解析逻辑（不调用 LLM）"""

    def setup_method(self):
        """每个测试前创建 ReportGenerator"""
        self.generator = ReportGenerator()

    def test_split_sections(self):
        """测试标题拆分逻辑"""
        text = """
## 1. 盈利能力分析
ROE 表现优秀，达到 25%。

## 2. 偿债能力分析
流动比率为 3.5，远高于安全线。

## 3. 综合结论
整体财务状况良好。
"""
        sections = self.generator._split_sections(text)

        assert "盈利能力分析" in sections
        assert "偿债能力分析" in sections
        assert "25%" in sections.get("盈利能力分析", "")

    def test_extract_list(self):
        """测试列表项提取"""
        text = """
### 核心优势：
- 盈利能力强
- 现金流充沛
- 品牌溢价高

### 主要劣势：
- 资产周转率偏低
"""
        strengths = self.generator._extract_list(text, "优势")
        weaknesses = self.generator._extract_list(text, "劣势")

        assert len(strengths) == 3
        assert "盈利能力强" in strengths
        assert len(weaknesses) == 1

    def test_generate_summary(self):
        """测试摘要生成"""
        text = """## 分析报告
该公司整体财务状况良好，盈利能力突出。

## 详细分析
..."""
        summary = self.generator._generate_summary(text)
        assert "财务状况良好" in summary

    def test_parse_response_basic(self):
        """测试基本响应解析"""
        mock_response = """
## 1. 盈利能力分析
ROE 达到 25%，表现优异。

## 2. 偿债能力分析
流动比率 3.5，偿债能力强。

## 3. 运营效率分析
资产周转率 0.5，效率一般。

## 4. 现金流分析
经营现金流充沛。

## 5. 杜邦分析解读
ROE 主要由高净利率驱动。

## 6. 综合结论

### 核心优势：
- 盈利能力极强
- 品牌护城河稳固

### 主要劣势：
- 资产周转率偏低

### 投资建议：
- 长期持有价值突出
"""
        report = self.generator._parse_response(
            raw_response=mock_response,
            stock_code="600519",
            stock_name="贵州茅台",
            report_date="2023-12-31",
        )

        assert report.stock_code == "600519"
        assert report.stock_name == "贵州茅台"
        assert report.report_date == "2023-12-31"
        assert len(report.strengths) >= 1
        assert len(report.weaknesses) >= 1


"""
====================================================================
【运行方式】

cd financial-report-analyzer
poetry run pytest tests/test_llm_engine.py -v

====================================================================
"""
