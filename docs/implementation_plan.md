# 📊 全新财务报表分析系统 — 总规划方案

## 项目定位

**从零构建一个完整的A股上市公司财务报表分析系统**，能够自动获取、清洗、分析、可视化三大报表（资产负债表、利润表、现金流量表），并借助 LLM 生成智能分析报告。全程使用中国信息源，避免网络/IP问题。

---

## 多 Skill 联合方案

本项目规划联合调用以下 Skills：

| Skill | 用途 |
|-------|------|
| `code-teaching-generator` | 每个模块按四层教学模型（基础→联合→高级→项目）输出，保姆级注释 |
| `github-project-analyzer` | 开发完成后自动生成项目结构文档、模块关联图 |
| `first_principles_teaching` | 财务分析核心概念（杜邦分析、自由现金流）的第一性原理教学 |
| `immersive-coding-tutor` | 关键模块的 5 阶段深度教学 |
| `mcp-builder` | 后续扩展：将分析能力包装为 MCP 服务 |
| `webapp-testing` | 前端界面的自动化测试 |

---

## 技术栈映射

全部从 [开发技术栈.md](file:///C:/Users/30847/Desktop/antigravity/开发技术栈.md) 中选型：

```
数据采集层：AKShare + requests
数据处理层：pandas + NumPy
数据验证层：pydantic（确保金额精度）
存储层：    MySQL（持久化）+ Redis（缓存）
分析引擎层：pandas + NumPy（财务比率计算）
LLM 分析层：LangChain + DeepSeek（智能分析报告）
API 层：    FastAPI
前端展示层：React + Tailwind CSS
可视化层：  matplotlib（后端图表）+ 前端图表库
日志层：    Loguru
报表导出：  openpyxl（Excel）
部署：      Docker + Nginx
```

---

## 项目结构设计

```
financial-report-analyzer/         # 项目根目录
├── README.md
├── pyproject.toml                 # Poetry 依赖管理
├── .env.example                   # 环境变量模板
├── .env                           # 实际环境变量（gitignored）
├── .gitignore
├── docker-compose.yml             # Docker 编排
│
├── src/                           # Python 后端源码
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   │
│   ├── config/                    # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py            # pydantic Settings 配置
│   │
│   ├── models/                    # pydantic 数据模型（所有数据结构定义）
│   │   ├── __init__.py
│   │   ├── financial_statements.py  # 三大报表数据模型
│   │   ├── financial_metrics.py     # 财务比率/指标模型
│   │   ├── analysis_result.py       # 分析结果模型
│   │   └── stock_info.py            # 股票基础信息模型
│   │
│   ├── data_fetcher/              # 数据采集层
│   │   ├── __init__.py
│   │   ├── akshare_client.py       # AKShare API 封装
│   │   ├── stock_list.py           # 股票列表获取
│   │   └── cache_manager.py        # Redis 缓存管理
│   │
│   ├── processor/                 # 数据处理与清洗层
│   │   ├── __init__.py
│   │   ├── data_cleaner.py         # 数据清洗（空值、异常值）
│   │   ├── data_validator.py       # 金额/数量精度验证
│   │   └── data_transformer.py     # 数据转换（中文列名→英文变量名）
│   │
│   ├── analyzer/                  # 核心分析引擎
│   │   ├── __init__.py
│   │   ├── ratio_calculator.py     # 财务比率计算（杜邦、偿债、运营）
│   │   ├── trend_analyzer.py       # 趋势分析（同比、环比、多年趋势）
│   │   ├── dupont_analyzer.py      # 杜邦分析专用模块
│   │   ├── cashflow_analyzer.py    # 现金流分析
│   │   └── peer_comparator.py      # 同行业对比分析
│   │
│   ├── llm_engine/                # LLM 智能分析层
│   │   ├── __init__.py
│   │   ├── llm_client.py           # LLM 客户端（LangChain）
│   │   ├── prompt_templates.py     # Prompt 模板
│   │   └── report_generator.py     # AI 分析报告生成
│   │
│   ├── api/                       # FastAPI 路由层
│   │   ├── __init__.py
│   │   ├── routes_stock.py         # 股票查询路由
│   │   ├── routes_analysis.py      # 分析路由
│   │   ├── routes_report.py        # 报告导出路由
│   │   └── dependencies.py         # 依赖注入
│   │
│   ├── storage/                   # 持久化存储层
│   │   ├── __init__.py
│   │   ├── database.py             # MySQL 连接管理
│   │   ├── crud.py                 # CRUD 操作
│   │   └── db_models.py            # SQLAlchemy ORM 模型
│   │
│   ├── export/                    # 报表导出
│   │   ├── __init__.py
│   │   ├── excel_exporter.py       # openpyxl Excel 导出
│   │   └── chart_generator.py      # matplotlib 图表生成
│   │
│   └── utils/                     # 通用工具
│       ├── __init__.py
│       ├── logger.py               # Loguru 日志配置
│       ├── precision.py            # 金额精度工具（Decimal）
│       └── naming_mapper.py        # 中英文变量名映射器
│
├── frontend/                      # 前端（Phase 2）
│   ├── package.json
│   ├── src/
│   └── ...
│
├── tests/                         # 测试
│   ├── test_data_fetcher.py
│   ├── test_processor.py
│   ├── test_analyzer.py
│   └── test_precision.py          # 金额精度专项测试
│
├── docs/                          # 文档
│   ├── variable_naming_table.md    # 变量命名中英对照表
│   ├── api_reference.md            # API 接口文档
│   └── class_method_reference.md   # 类/方法标准表
│
└── learning-docs/                 # 教学文档（github-project-analyzer 输出）
```

---

## 核心数据模型设计

### 三大报表 pydantic 模型

> [!IMPORTANT]
> 所有金额字段使用 `Decimal` 类型而非 `float`，确保精度不丢失。这是你第 9 条要求的核心方案。

```python
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class BalanceSheet(BaseModel):
    """资产负债表"""
    stock_code: str = Field(..., description="股票代码 / Stock Code")
    report_date: date = Field(..., description="报告期 / Report Date")
    
    # 资产
    total_current_assets: Decimal = Field(default=Decimal("0"), description="流动资产合计")
    total_non_current_assets: Decimal = Field(default=Decimal("0"), description="非流动资产合计")
    total_assets: Decimal = Field(default=Decimal("0"), description="资产总计")
    
    # 负债
    total_current_liabilities: Decimal = Field(default=Decimal("0"), description="流动负债合计")
    total_non_current_liabilities: Decimal = Field(default=Decimal("0"), description="非流动负债合计")
    total_liabilities: Decimal = Field(default=Decimal("0"), description="负债合计")
    
    # 所有者权益
    total_equity: Decimal = Field(default=Decimal("0"), description="所有者权益合计")

class IncomeStatement(BaseModel):
    """利润表"""
    stock_code: str
    report_date: date
    
    total_revenue: Decimal = Field(default=Decimal("0"), description="营业总收入")
    operating_cost: Decimal = Field(default=Decimal("0"), description="营业总成本")
    operating_profit: Decimal = Field(default=Decimal("0"), description="营业利润")
    total_profit: Decimal = Field(default=Decimal("0"), description="利润总额")
    net_income: Decimal = Field(default=Decimal("0"), description="净利润")

class CashFlowStatement(BaseModel):
    """现金流量表"""
    stock_code: str
    report_date: date
    
    operating_cashflow: Decimal = Field(default=Decimal("0"), description="经营活动现金流量净额")
    investing_cashflow: Decimal = Field(default=Decimal("0"), description="投资活动现金流量净额")
    financing_cashflow: Decimal = Field(default=Decimal("0"), description="筹资活动现金流量净额")
    net_cashflow: Decimal = Field(default=Decimal("0"), description="现金净增加额")
```

---

## 变量命名中英文对照表（核心片段）

> 完整版将作为 [docs/variable_naming_table.md](file:///C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/variable_naming_table.md) 独立文件输出。

### 三大报表核心字段

| 中文 | 英文变量名 | 类型 | AKShare 原始列名 | 模糊检索别名 |
|------|-----------|------|------------------|-------------|
| 股票代码 | `stock_code` | `str` | `代码` | 证券代码, 股票号 |
| 报告期 | `report_date` | `date` | `日期` | 报表日期, 财报日期 |
| **资产负债表** | | | | |
| 流动资产合计 | `total_current_assets` | `Decimal` | `流动资产合计` | 流动资产总额 |
| 非流动资产合计 | `total_non_current_assets` | `Decimal` | `非流动资产合计` | 长期资产合计 |
| 资产总计 | `total_assets` | `Decimal` | `资产总计` | 总资产, 资产合计 |
| 流动负债合计 | `total_current_liabilities` | `Decimal` | `流动负债合计` | 短期负债合计 |
| 非流动负债合计 | `total_non_current_liabilities` | `Decimal` | `非流动负债合计` | 长期负债合计 |
| 负债合计 | `total_liabilities` | `Decimal` | `负债合计` | 总负债, 负债总额 |
| 所有者权益合计 | `total_equity` | `Decimal` | `所有者权益合计` | 股东权益, 净资产 |
| **利润表** | | | | |
| 营业总收入 | `total_revenue` | `Decimal` | `营业总收入` | 营收, 总收入 |
| 营业总成本 | `operating_cost` | `Decimal` | `营业总成本` | 总成本 |
| 营业利润 | `operating_profit` | `Decimal` | `营业利润` | 经营利润 |
| 利润总额 | `total_profit` | `Decimal` | `利润总额` | 税前利润 |
| 净利润 | `net_income` | `Decimal` | `净利润` | 纯利润, 纯利 |
| **现金流量表** | | | | |
| 经营活动现金流量净额 | `operating_cashflow` | `Decimal` | `经营活动产生的现金流量净额` | 经营现金流 |
| 投资活动现金流量净额 | `investing_cashflow` | `Decimal` | `投资活动产生的现金流量净额` | 投资现金流 |
| 筹资活动现金流量净额 | `financing_cashflow` | `Decimal` | `筹资活动产生的现金流量净额` | 融资现金流 |
| **财务比率** | | | | |
| 净资产收益率 | `roe` / `return_on_equity` | `Decimal` | `净资产收益率(%)` | ROE |
| 资产负债率 | `debt_to_asset_ratio` | `Decimal` | `资产负债率(%)` | 负债率 |
| 流动比率 | `current_ratio` | `Decimal` | `流动比率` | — |
| 市盈率 | `pe_ratio` | `float` | `市盈率-动态` | PE, P/E |
| 市净率 | `pb_ratio` / `price_to_book` | `float` | `市净率` | PB, P/B |
| 销售净利率 | `net_profit_margin` | `Decimal` | `销售净利率(%)` | 净利润率 |

### 分析相关

| 中文 | 英文变量名 | 类型 | 说明 |
|------|-----------|------|------|
| 杜邦分析结果 | `dupont_result` | `DuPontResult` | 杜邦分析拆解结果 |
| 趋势分析 | `trend_result` | `TrendResult` | 同比/环比趋势 |
| 同比增长率 | `yoy_growth` | `Decimal` | Year-over-Year |
| 环比增长率 | `qoq_growth` | `Decimal` | Quarter-over-Quarter |
| 自由现金流 | `free_cash_flow` | `Decimal` | FCF = 经营现金流 - 资本支出 |

---

## 核心类/方法标准表

> 只列出**会被跨模块调用的关键类和方法**。

### 数据采集层 (`data_fetcher/`)

| 类/函数 | 方法 | 输入 | 输出 | 被谁调用 |
|---------|------|------|------|---------|
| `AKShareClient` | `fetch_balance_sheet(stock_code: str)` | 股票代码 `str` | `List[BalanceSheet]` | `processor/`, `analyzer/` |
| `AKShareClient` | `fetch_income_statement(stock_code: str)` | 股票代码 `str` | `List[IncomeStatement]` | `processor/`, `analyzer/` |
| `AKShareClient` | `fetch_cashflow_statement(stock_code: str)` | 股票代码 `str` | `List[CashFlowStatement]` | `processor/`, `analyzer/` |
| `AKShareClient` | `fetch_financial_indicators(stock_code: str)` | 股票代码 `str` | `Dict[str, Any]` | `analyzer/` |
| `AKShareClient` | `fetch_stock_list()` | 无 | `List[StockInfo]` | `api/` |
| `CacheManager` | [get(key: str)](file:///C:/Users/30847/Desktop/antigravity/%E6%8A%80%E6%9C%AF%E6%A0%88%E6%95%99%E5%AD%A6%E5%90%88%E8%AE%A1/A_Share_investment_Agent/src/tools/api.py#591-607) | 缓存键 `str` | `Optional[Any]` | 所有层 |
| `CacheManager` | `set(key: str, value: Any, ttl: int)` | 键, 值, 过期秒数 | `None` | 所有层 |

### 数据处理层 (`processor/`)

| 类/函数 | 方法 | 输入 | 输出 | 被谁调用 |
|---------|------|------|------|---------|
| `DataCleaner` | `clean_financial_data(df: pd.DataFrame)` | 原始 DataFrame | 清洗后 DataFrame | `analyzer/` |
| `DataValidator` | `validate_amounts(data: BaseModel)` | pydantic 模型实例 | `ValidationResult` | 所有层 |
| `DataTransformer` | `chinese_to_english(df: pd.DataFrame)` | 中文列名 DataFrame | 英文列名 DataFrame | `data_fetcher/` |

### 分析引擎层 (`analyzer/`)

| 类/函数 | 方法 | 输入 | 输出 | 被谁调用 |
|---------|------|------|------|---------|
| `RatioCalculator` | `calc_profitability(bs, is_)` | 资产负债表, 利润表 | `ProfitabilityMetrics` | `api/`, `llm_engine/` |
| `RatioCalculator` | `calc_solvency(bs)` | 资产负债表 | `SolvencyMetrics` | `api/`, `llm_engine/` |
| `RatioCalculator` | `calc_efficiency(bs, is_)` | 资产负债表, 利润表 | `EfficiencyMetrics` | `api/`, `llm_engine/` |
| `DuPontAnalyzer` | `analyze(bs, is_)` | 资产负债表, 利润表 | `DuPontResult` | `api/`, `llm_engine/` |
| `CashFlowAnalyzer` | `analyze(cf, is_)` | 现金流量表, 利润表 | `CashFlowResult` | `api/`, `llm_engine/` |
| `TrendAnalyzer` | `calc_yoy(current, previous)` | 当期, 同期 | `Decimal` | `api/` |
| `PeerComparator` | `compare(stock_code, peer_codes)` | 目标代码, 对标代码列表 | `ComparisonResult` | `api/` |

### LLM 分析层 (`llm_engine/`)

| 类/函数 | 方法 | 输入 | 输出 | 被谁调用 |
|---------|------|------|------|---------|
| `LLMClient` | `analyze(prompt: str)` | Prompt 文本 | `str`（分析文本） | `ReportGenerator` |
| `ReportGenerator` | `generate_report(stock_code, all_metrics)` | 代码, 全部指标 | `AnalysisReport` | `api/` |

### API 层 (`api/`)

| 路由 | 方法 | 输入 | 输出 |
|------|------|------|------|
| `GET /api/stocks` | 获取股票列表 | 查询参数 | `List[StockInfo]` |
| `GET /api/stocks/{code}/statements` | 获取三大报表 | 股票代码 | 三大报表数据 |
| `GET /api/stocks/{code}/ratios` | 获取财务比率 | 股票代码 | 全部比率指标 |
| `GET /api/stocks/{code}/dupont` | 杜邦分析 | 股票代码 | `DuPontResult` |
| `GET /api/stocks/{code}/trend` | 趋势分析 | 股票代码 + 年份范围 | `TrendResult` |
| `POST /api/stocks/{code}/ai-report` | AI 分析报告 | 股票代码 + 分析深度 | `AnalysisReport` |
| `GET /api/stocks/{code}/export/excel` | 导出 Excel | 股票代码 | `.xlsx` 文件流 |

---

## API / Cookie / 数据源需求

> [!TIP]
> **好消息：AKShare 不需要任何 API Key 或 Cookie！** 它直接从公开数据源（新浪财经、东方财富）爬取数据，免费且无需注册。

### 你需要准备的

| 项目 | 是否必须 | 说明 |
|------|---------|------|
| **AKShare** | ✅ 必须 | `pip install akshare`，无需 API Key |
| **LLM API Key** | ✅ 必须 | **DeepSeek API**（已确认）`https://api.deepseek.com` |
| **MySQL** | ✅ 必须 | 本机安装或 Docker 部署 |
| **Redis** | ⚡ 推荐 | 缓存层，Docker 一行部署：`docker run -d -p 6379:6379 redis` |
| **Cookie** | ❌ 不需要 | AKShare 自动处理，无需手动抓 Cookie |

### 全部中国信息源（第 7 条要求）

| 数据类型 | 来源 | AKShare 接口 |
|---------|------|-------------|
| 资产负债表 | 新浪财经 | `stock_financial_report_sina(stock, symbol="资产负债表")` |
| 利润表 | 新浪财经 | `stock_financial_report_sina(stock, symbol="利润表")` |
| 现金流量表 | 新浪财经 | `stock_financial_report_sina(stock, symbol="现金流量表")` |
| 财务指标 | 新浪财经 | `stock_financial_analysis_indicator(symbol)` |
| 实时行情 | 东方财富 | `stock_zh_a_spot_em()` |
| 历史行情 | 东方财富 | `stock_zh_a_hist(symbol)` |
| 股票列表 | 东方财富 | `stock_zh_a_spot_em()` 列表 |
| 行业分类 | 东方财富 | `stock_board_industry_name_em()` |

> 全部走国内 CDN，不受 VPN/IP 影响 ✅

---

## 金额精度控制方案（第 9 条要求）

> [!CAUTION]
> **金额数据绝不能用 `float`！** Python `float` 会造成精度丢失（如 `0.1 + 0.2 ≠ 0.3`）。必须用 `Decimal`。

### 四层精度校验

```
1. 采集层：AKShare 返回值 → 立即转 Decimal
2. 验证层：pydantic validator 强制校验
3. 计算层：所有比率计算用 Decimal 运算
4. 输出层：显示/导出时统一保留位数
```

### 实现方案（`utils/precision.py`）

```python
from decimal import Decimal, ROUND_HALF_UP

# 金额保留2位（元），比率保留4位（如 0.1234 = 12.34%）
AMOUNT_PRECISION = Decimal("0.01")
RATIO_PRECISION = Decimal("0.0001")

def to_amount(value) -> Decimal:
    """安全转换为金额精度"""
    return Decimal(str(value)).quantize(AMOUNT_PRECISION, rounding=ROUND_HALF_UP)

def to_ratio(value) -> Decimal:
    """安全转换为比率精度"""
    return Decimal(str(value)).quantize(RATIO_PRECISION, rounding=ROUND_HALF_UP)
```

---

## 函数输入输出文档规范（第 2 条要求）

每个脚本文件的**文件头**和**文件尾**将包含如下格式的接口说明：

```python
"""
====================================================================
模块名称：ratio_calculator.py
模块功能：计算各类财务比率（盈利能力、偿债能力、运营效率）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_profitability()         │ bs: BalanceSheet,           │ ProfitabilityMetrics     │
│                              │ is_: IncomeStatement        │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_solvency()              │ bs: BalanceSheet            │ SolvencyMetrics          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_efficiency()            │ bs: BalanceSheet,           │ EfficiencyMetrics        │
│                              │ is_: IncomeStatement        │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 api/routes_analysis.py 调用（提供 REST API）
→ 被 llm_engine/report_generator.py 调用（AI报告生成）
→ 被 export/excel_exporter.py 调用（Excel导出）
====================================================================
"""
```

---

## 实施路线（分 3 个 Phase）

### Phase 1：核心后端（本次重点）

1. 项目骨架 + 配置管理
2. `models/` — pydantic 数据模型（全 Decimal）
3. `data_fetcher/` — AKShare 封装 + Redis 缓存
4. `processor/` — 清洗、验证、中英文转换
5. `analyzer/` — 财务比率 + 杜邦 + 趋势
6. `api/` — FastAPI 路由
7. `utils/` — 日志、精度、命名映射
8. `tests/` — 单元测试 + 精度测试
9. `docs/` — 变量表、类方法表、API 文档

### Phase 2：LLM + 导出

1. `llm_engine/` — LangChain 智能分析
2. `export/` — Excel 报表 + matplotlib 图表

### Phase 3：前端 + 部署

1. `frontend/` — React/Vue + Tailwind
2. Docker + Nginx 部署

---

## 关于 Git 使用（第 8 条要求）

项目从一开始就初始化 Git，每完成一个模块做一次 commit。你可以随时用以下命令查看修改对比：

```powershell
# 查看当前所有修改
git diff

# 查看某个文件的修改
git diff src/analyzer/ratio_calculator.py

# 查看最近 N 次提交历史
git log -n 5 --oneline

# 查看某次提交的详细修改
git show <commit-hash>
```

---

## 验证计划

### 自动测试

```powershell
# 1. 数据采集测试 — 验证 AKShare 接口能正常返回数据
cd financial-report-analyzer
poetry run pytest tests/test_data_fetcher.py -v

# 2. 数据处理测试 — 验证清洗/转换结果正确
poetry run pytest tests/test_processor.py -v

# 3. 分析引擎测试 — 验证财务比率计算正确（硬编码已知数据对比）
poetry run pytest tests/test_analyzer.py -v

# 4. 金额精度专项测试 — 验证 Decimal 精度无丢失
poetry run pytest tests/test_precision.py -v

# 5. API 端到端测试
poetry run pytest tests/test_api.py -v

# 6. 全部测试
poetry run pytest tests/ -v
```

### 手动验证

1. **数据准确性**：取一只已知股票（如 `600519` 贵州茅台），对比系统输出和东方财富网页上的实际数据
2. **精度验证**：计算 `总资产 = 流动资产 + 非流动资产`，验证等式两边精确相等
3. **API 测试**：启动 FastAPI 后访问 `http://localhost:8000/docs`，调用各接口看返回数据

---

## User Review Required

> [!NOTE]
> **已确认的技术选型**：
> - ✅ 前端：**React** + Tailwind CSS
> - ✅ LLM：**DeepSeek**（国内 API，`https://api.deepseek.com`）
> - ✅ 数据库：**MySQL**（本机已安装）
> - ✅ 项目位置：`C:\Users\30847\Desktop\antigravity\financial-report-analyzer\`
> - ✅ 先做 Phase 1（核心后端），文档先行

## 规范文档清单

以下文档已就绪：
- ✅ [变量命名对照表](file:///C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/variable_naming_table.md)
- ✅ [类/方法标准表](file:///C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/class_method_reference.md)
- ✅ [MySQL 使用指南](file:///C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/mysql_guide.md)
- ✅ [编码规范](file:///C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/coding_conventions.md)
