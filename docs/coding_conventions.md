# 📐 编码规范与项目约定 (Coding Conventions)

> **适用范围**：`financial-report-analyzer` 项目全局

---

## 一、语言与命名

| 类别 | 规则 | 示例 |
|------|------|------|
| Python 变量/函数 | `snake_case` | `total_assets`, `calc_roe()` |
| Python 类名 | `PascalCase` | `BalanceSheet`, `RatioCalculator` |
| Python 常量 | `UPPER_SNAKE` | `AMOUNT_PRECISION`, `CACHE_TTL` |
| React 组件 | `PascalCase` | `StockDetail`, `RatioChart` |
| React 变量/函数 | `camelCase` | `totalAssets`, `fetchData()` |
| 文件名 | `snake_case.py` / `PascalCase.tsx` | `ratio_calculator.py`, `StockDetail.tsx` |
| API 路由 | `kebab-case` 或 `snake_case` | `/api/stocks/{code}/ai-report` |
| 数据库表名 | `snake_case` 复数 | `balance_sheets`, `analysis_reports` |
| 数据库列名 | `snake_case` | `total_assets`, `stock_code` |

---

## 二、函数文档标准（每个文件必须遵守）

### 文件头模板

每个 `.py` 文件的**最顶部**必须包含：

```python
"""
====================================================================
模块名称：<文件名.py>
模块功能：<一句话描述>
所属层级：<data_fetcher / processor / analyzer / llm_engine / api / export / utils>

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ <函数1>                      │ <参数: 类型>                │ <返回类型>               │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ <函数2>                      │ <参数: 类型>                │ <返回类型>               │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
← 被谁调用：<调用方模块>
→ 调用了谁：<被调用模块>
→ 输出到哪：<下游消费者>
====================================================================
"""
```

### 函数级 Docstring 模板

```python
def calc_roe(bs: BalanceSheet, is_: IncomeStatement) -> Decimal:
    """计算净资产收益率 (ROE)
    
    公式：ROE = 净利润 / 所有者权益合计
    
    Args:
        bs: 资产负债表实例，需要 total_equity 字段
        is_: 利润表实例，需要 net_income 字段
    
    Returns:
        Decimal: ROE 值，保留4位小数（如 0.1234 表示 12.34%）
    
    Raises:
        ZeroDivisionError: 当 total_equity 为 0 时
    
    Example:
        >>> calc_roe(bs, is_)
        Decimal('0.1543')
    
    数据流向:
        → 被 routes_analysis.py 调用
        → 被 report_generator.py 调用
    """
```

---

## 三、金额精度规范

| 规则 | 说明 |
|------|------|
| ✅ 所有金额使用 `Decimal` | 不允许用 `float` 存储任何金额 |
| ✅ AKShare 返回值立即转 `Decimal(str(value))` | 先转 `str` 再转 `Decimal`，避免浮点中间态 |
| ✅ 金额保留 2 位小数 | `quantize(Decimal("0.01"))` |
| ✅ 比率保留 4 位小数 | `quantize(Decimal("0.0001"))` |
| ✅ 除法前检查除数是否为 0 | 返回 `Decimal("0")` 而非报错 |
| ✅ 数据库用 `DECIMAL(20,2)` | 不用 `FLOAT` 或 `DOUBLE` |
| ❌ 禁止 `float(value)` 处理金额 | 会丢失精度 |
| ❌ 禁止 `round()` 做金额舍入 | 用 `Decimal.quantize()` |

---

## 四、日志规范

使用 **Loguru**（已在技术栈中）：

```python
from loguru import logger

# 日志级别使用规范
logger.debug("调试信息：变量值 {}", value)      # 开发时用
logger.info("正常流程：获取 {} 的资产负债表", stock_code)  # 关键步骤
logger.warning("异常但不致命：{} 数据为空，使用默认值", field)  # 可恢复
logger.error("错误：获取数据失败 {}", str(e))    # 需要排查
logger.critical("严重：数据库连接丢失")           # 系统级故障
```

### 日志文件配置

```python
# src/utils/logger.py
from loguru import logger
import sys

logger.remove()  # 移除默认handler
logger.add(sys.stderr, level="INFO")  # 控制台输出
logger.add(
    "logs/{time:YYYY-MM-DD}.log",     # 按天分割
    rotation="00:00",                  # 每天午夜轮转
    retention="30 days",               # 保留30天
    encoding="utf-8",
    level="DEBUG",
)
```

---

## 五、错误处理规范

```python
# ✅ 正确做法：具体异常 + 有意义的错误信息
try:
    data = ak.stock_financial_report_sina(stock=f"sh{stock_code}", symbol="资产负债表")
except Exception as e:
    logger.error(f"获取 {stock_code} 资产负债表失败: {e}")
    raise DataFetchError(f"AKShare 资产负债表接口异常: {stock_code}") from e

# ❌ 错误做法：静默吞掉异常
try:
    data = ak.stock_financial_report_sina(...)
except:
    data = pd.DataFrame()  # 吞掉异常，下游不知道为什么没数据
```

---

## 六、Git Commit 规范

```
<类型>: <简要描述>

类型列表：
feat:     新功能
fix:      修复 bug
docs:     文档更新
refactor: 重构（不改功能）
test:     测试相关
chore:    构建/依赖/配置
```

示例：

```
feat: 实现 AKShareClient.fetch_balance_sheet
fix: 修复 ROE 计算除零错误
docs: 完善变量命名对照表
test: 添加金额精度测试用例
```

---

## 七、项目目录约定

| 目录 | 放什么 | 不放什么 |
|------|--------|---------|
| `src/models/` | pydantic 模型 | 业务逻辑 |
| `src/data_fetcher/` | 数据获取 | 数据分析 |
| `src/processor/` | 清洗/验证/转换 | API 路由 |
| `src/analyzer/` | 分析计算逻辑 | 数据获取 |
| `src/api/` | FastAPI 路由 | 复杂计算 |
| `src/utils/` | 通用工具 | 业务逻辑 |
| `tests/` | 测试文件 | 生产代码 |
| `docs/` | 规范文档 | 代码文件 |

---

## 八、pydantic 模型规范

```python
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import date

class BalanceSheet(BaseModel):
    """资产负债表 (Balance Sheet)"""
    
    # 必填字段用 ... 标记
    stock_code: str = Field(..., description="股票代码 / Stock Code", example="600519")
    report_date: date = Field(..., description="报告期 / Report Date")
    
    # 金额字段用 Decimal + 默认值 0
    total_assets: Decimal = Field(
        default=Decimal("0"), 
        description="资产总计 / Total Assets"
    )
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),  # JSON 序列化时保持精度
        }
```

---

## 九、API 响应格式统一

所有 API 返回统一格式：

```python
# 成功
{
    "code": 200,
    "message": "success",
    "data": { ... }  # 实际数据
}

# 错误
{
    "code": 400,  # 或 404, 500
    "message": "股票代码不存在: 999999",
    "data": null
}
```
