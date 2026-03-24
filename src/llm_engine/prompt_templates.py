"""
====================================================================
模块名称：prompt_templates.py
模块功能：财务分析 Prompt 模板（中文专业版）

【模板清单】
- SYSTEM_PROMPT: 系统角色设定（专业财务分析师）
- COMPREHENSIVE_ANALYSIS_TEMPLATE: 综合财务分析模板
- SINGLE_METRIC_TEMPLATE: 单项指标深度分析模板

【数据流向】
→ 被 llm_engine/report_generator.py 使用
====================================================================
"""

from langchain_core.prompts import PromptTemplate


# ============================================================
# 系统角色 Prompt
# ============================================================

SYSTEM_PROMPT = """你是一名资深的中国A股上市公司财务分析师，拥有 CFA 和 CPA 资质。
你的分析风格：
1. 数据驱动：所有结论必须有具体数据支撑
2. 专业严谨：使用标准财务术语，逻辑清晰
3. 通俗易懂：在专业的基础上，让非财务背景的投资者也能理解
4. 风险导向：重点关注潜在风险和异常指标
5. 对比视角：将指标与行业平均水平或标杆企业对比

输出格式要求：
- 使用中文回答
- 分段落组织，每段有小标题
- 关键数据用【】标注
- 分析结论要明确，不要模棱两可
"""


# ============================================================
# 综合财务分析模板
# ============================================================

COMPREHENSIVE_ANALYSIS_TEMPLATE = PromptTemplate(
    input_variables=[
        "stock_code",
        "stock_name",
        "report_date",
        "profitability_data",
        "solvency_data",
        "efficiency_data",
        "cashflow_data",
        "dupont_data",
        "trend_data",
    ],
    template="""请对以下A股上市公司进行全面的财务分析：

## 基础信息
- 股票代码：{stock_code}
- 股票名称：{stock_name}
- 报告期：{report_date}

## 盈利能力指标
{profitability_data}

## 偿债能力指标
{solvency_data}

## 运营效率指标
{efficiency_data}

## 现金流分析
{cashflow_data}

## 杜邦分析（ROE 拆解）
{dupont_data}

## 趋势变化
{trend_data}

---

请从以下六个维度进行深入分析，并最终给出综合评估：

### 1. 盈利能力分析
分析 ROE、ROA、净利率、毛利率的水平和变化趋势，评估盈利质量。

### 2. 偿债能力分析
分析流动比率、速动比率、资产负债率，评估短期和长期偿债风险。

### 3. 运营效率分析
分析资产周转率、权益乘数，评估资产使用效率。

### 4. 现金流分析
分析经营现金流、自由现金流、现金利润比，评估盈利的"含金量"。

### 5. 杜邦分析解读
基于 ROE = 净利率 × 资产周转率 × 权益乘数，分析 ROE 的驱动因素。

### 6. 趋势与风险
识别关键指标的变化趋势，提示潜在风险点。

### 7. 综合结论
- 列出 3-5 个核心优势
- 列出 2-3 个主要劣势或风险
- 给出 2-3 条投资建议

请确保每个维度都引用具体数据进行分析。
""",
)


# ============================================================
# 单项指标深度分析模板
# ============================================================

SINGLE_METRIC_TEMPLATE = PromptTemplate(
    input_variables=["stock_name", "metric_name", "metric_value", "context"],
    template="""请对 {stock_name} 的 {metric_name} 进行深度分析：

当前值：{metric_value}

相关背景信息：
{context}

请分析：
1. 该指标当前水平在行业中处于什么位置？
2. 该指标的变化趋势意味着什么？
3. 有哪些潜在的风险或机会？
""",
)


def format_metrics_for_prompt(metrics_dict: dict) -> str:
    """
    将指标字典格式化为 Prompt 可读的文本

    Args:
        metrics_dict: 指标名-值字典

    Returns:
        str: 格式化后的文本

    Examples:
        >>> data = {"ROE": "0.1500", "ROA": "0.0800"}
        >>> print(format_metrics_for_prompt(data))
        - ROE: 0.1500
        - ROA: 0.0800
    """
    lines = []
    for key, value in metrics_dict.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


"""
====================================================================
【使用示例】

from src.llm_engine.prompt_templates import (
    SYSTEM_PROMPT,
    COMPREHENSIVE_ANALYSIS_TEMPLATE,
    format_metrics_for_prompt,
)

# 1. 渲染综合分析 Prompt
prompt = COMPREHENSIVE_ANALYSIS_TEMPLATE.format(
    stock_code="600519",
    stock_name="贵州茅台",
    report_date="2023-12-31",
    profitability_data="- ROE: 25.00%\n- ROA: 18.00%",
    solvency_data="- 流动比率: 3.50\n- 资产负债率: 20.00%",
    efficiency_data="- 总资产周转率: 0.50",
    cashflow_data="- 经营现金流: 500亿元",
    dupont_data="- ROE = 30% × 0.5 × 1.67",
    trend_data="- 净利润同比增长 15%",
)

====================================================================
"""
