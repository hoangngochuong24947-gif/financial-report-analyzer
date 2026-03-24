"""
====================================================================
模块名称：chart_generator.py
模块功能：使用 matplotlib 生成财务分析图表

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ generate_trend_chart()       │ 指标名, 数据列表             │ bytes (PNG)             │
│ generate_ratio_bar_chart()   │ 指标字典                    │ bytes (PNG)             │
│ generate_dupont_chart()      │ DuPontResult               │ bytes (PNG)             │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 export/excel_exporter.py 调用（嵌入 Excel）
→ 被 api/routes_report.py 调用（独立 PNG 下载）
====================================================================
"""

import io
from decimal import Decimal
from typing import List, Dict, Tuple, Optional

import matplotlib
matplotlib.use("Agg")  # 非 GUI 后端，适合服务器环境
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from src.models.financial_metrics import DuPontResult
from src.utils.logger import logger


# ============================================================
# 字体配置（支持中文显示）
# ============================================================

def _setup_chinese_font():
    """配置 matplotlib 中文字体"""
    # 尝试常见的中文字体
    chinese_fonts = ["SimHei", "Microsoft YaHei", "SimSun", "KaiTi", "FangSong"]
    for font_name in chinese_fonts:
        try:
            fm.findfont(font_name, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [font_name]
            plt.rcParams["axes.unicode_minus"] = False
            logger.debug(f"Using Chinese font: {font_name}")
            return
        except Exception:
            continue

    # 找不到中文字体时的降级方案
    logger.warning("No Chinese font found. Charts may not display Chinese characters correctly.")
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_setup_chinese_font()

# 配色方案（专业蓝色系）
COLORS = ["#2F5496", "#4472C4", "#5B9BD5", "#A5C8E1", "#D6E4F0"]
ACCENT_COLOR = "#E74C3C"


def generate_trend_chart(
    metric_name: str,
    dates: List[str],
    values: List[float],
    title: Optional[str] = None,
) -> bytes:
    """
    生成趋势折线图

    Args:
        metric_name: 指标名称（如 "净利润"）
        dates: 日期列表（如 ["2021", "2022", "2023"]）
        values: 对应数值列表
        title: 图表标题（可选，默认自动生成）

    Returns:
        bytes: PNG 图片二进制内容

    Examples:
        >>> png_data = generate_trend_chart(
        ...     "净利润", ["2021", "2022", "2023"], [500, 600, 700]
        ... )
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(dates, values, marker="o", linewidth=2.5, color=COLORS[0],
            markersize=8, markerfacecolor=COLORS[1])

    # 在数据点上标注数值
    for i, (d, v) in enumerate(zip(dates, values)):
        ax.annotate(
            f"{v:,.0f}",
            (d, v),
            textcoords="offset points",
            xytext=(0, 12),
            ha="center",
            fontsize=9,
            color=COLORS[0],
            fontweight="bold",
        )

    ax.set_title(title or f"{metric_name} — 趋势分析", fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("报告期", fontsize=12)
    ax.set_ylabel(metric_name, fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    logger.info(f"Trend chart generated: {metric_name}")
    return buffer.getvalue()


def generate_ratio_bar_chart(
    ratios: Dict[str, float],
    title: str = "财务比率分析",
) -> bytes:
    """
    生成财务比率柱状图

    Args:
        ratios: 指标名-值字典（如 {"ROE": 0.15, "ROA": 0.08}）
        title: 图表标题

    Returns:
        bytes: PNG 图片二进制内容
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    names = list(ratios.keys())
    values = list(ratios.values())
    bar_colors = COLORS[:len(values)] if len(values) <= len(COLORS) else [COLORS[0]] * len(values)

    bars = ax.bar(names, values, color=bar_colors, width=0.6, edgecolor="white", linewidth=0.5)

    # 在柱子上方标注数值
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.02,
            f"{value:.2%}",
            ha="center",
            fontsize=10,
            fontweight="bold",
            color=COLORS[0],
        )

    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_ylabel("比率", fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    logger.info(f"Ratio bar chart generated: {title}")
    return buffer.getvalue()


def generate_dupont_chart(dupont: DuPontResult, stock_name: str = "") -> bytes:
    """
    生成杜邦分析分解图（水平柱状 + 乘法关系）

    Args:
        dupont: 杜邦分析结果
        stock_name: 股票名称

    Returns:
        bytes: PNG 图片二进制内容
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    factors = ["销售净利率", "总资产周转率", "权益乘数"]
    values = [
        float(dupont.net_profit_margin),
        float(dupont.asset_turnover),
        float(dupont.equity_multiplier),
    ]

    bars = ax.barh(factors, values, color=COLORS[:3], height=0.5, edgecolor="white")

    # 标注数值
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.4f}",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=COLORS[0],
        )

    roe_value = float(dupont.roe)
    title = f"{stock_name} 杜邦分析" if stock_name else "杜邦分析"
    ax.set_title(
        f"{title}\nROE = {roe_value:.2%}",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("数值", fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.3)

    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    logger.info(f"DuPont chart generated for {stock_name}")
    return buffer.getvalue()


"""
====================================================================
【使用示例】

from src.export.chart_generator import (
    generate_trend_chart,
    generate_ratio_bar_chart,
    generate_dupont_chart,
)

# 1. 趋势图
png = generate_trend_chart(
    "净利润（亿元）",
    ["2020", "2021", "2022", "2023"],
    [466, 524, 592, 640],
)
with open("trend.png", "wb") as f:
    f.write(png)

# 2. 比率柱状图
png = generate_ratio_bar_chart(
    {"ROE": 0.25, "ROA": 0.18, "净利率": 0.30, "毛利率": 0.91},
    title="贵州茅台 — 盈利能力分析",
)

# 3. 杜邦分析图
png = generate_dupont_chart(dupont_result, "贵州茅台")

====================================================================
"""
