# 📋 变量命名中英文对照表 (Variable Naming Table)

> **适用范围**：`financial-report-analyzer` 项目全局统一命名标准  
> **命名规则**：Python 使用 `snake_case`，React 使用 `camelCase`

---

## 一、资产负债表 (Balance Sheet)

| 中文 | 英文变量名 | 类型 | AKShare 原始列名 | 模糊检索别名 |
|------|-----------|------|------------------|-------------|
| 货币资金 | `cash_and_equivalents` | `Decimal` | `货币资金` | 现金, 银行存款 |
| 应收票据 | `notes_receivable` | `Decimal` | `应收票据` | — |
| 应收账款 | `accounts_receivable` | `Decimal` | `应收账款` | 应收款 |
| 预付款项 | `prepayments` | `Decimal` | `预付款项` | 预付账款 |
| 存货 | `inventory` | `Decimal` | `存货` | 库存 |
| 其他流动资产 | `other_current_assets` | `Decimal` | `其他流动资产` | — |
| **流动资产合计** | `total_current_assets` | `Decimal` | `流动资产合计` | 流动资产总额 |
| 固定资产 | `fixed_assets` | `Decimal` | `固定资产` | — |
| 在建工程 | `construction_in_progress` | `Decimal` | `在建工程` | — |
| 无形资产 | `intangible_assets` | `Decimal` | `无形资产` | — |
| 商誉 | `goodwill` | `Decimal` | `商誉` | — |
| 长期股权投资 | `long_term_equity_investment` | `Decimal` | `长期股权投资` | — |
| 其他非流动资产 | `other_non_current_assets` | `Decimal` | `其他非流动资产` | — |
| **非流动资产合计** | `total_non_current_assets` | `Decimal` | `非流动资产合计` | 长期资产合计 |
| **资产总计** | `total_assets` | `Decimal` | `资产总计` | 总资产, 资产合计 |
| 短期借款 | `short_term_borrowings` | `Decimal` | `短期借款` | 短期贷款 |
| 应付票据 | `notes_payable` | `Decimal` | `应付票据` | — |
| 应付账款 | `accounts_payable` | `Decimal` | `应付账款` | 应付款 |
| 预收款项 | `advances_from_customers` | `Decimal` | `预收款项` | 预收账款 |
| 应付职工薪酬 | `employee_benefits_payable` | `Decimal` | `应付职工薪酬` | 应付工资 |
| 应交税费 | `taxes_payable` | `Decimal` | `应交税费` | 应交税金 |
| **流动负债合计** | `total_current_liabilities` | `Decimal` | `流动负债合计` | 短期负债合计 |
| 长期借款 | `long_term_borrowings` | `Decimal` | `长期借款` | 长期贷款 |
| 应付债券 | `bonds_payable` | `Decimal` | `应付债券` | — |
| **非流动负债合计** | `total_non_current_liabilities` | `Decimal` | `非流动负债合计` | 长期负债合计 |
| **负债合计** | `total_liabilities` | `Decimal` | `负债合计` | 总负债 |
| 实收资本(或股本) | `paid_in_capital` | `Decimal` | `实收资本(或股本)` | 股本, 注册资本 |
| 资本公积 | `capital_reserve` | `Decimal` | `资本公积` | — |
| 盈余公积 | `surplus_reserve` | `Decimal` | `盈余公积` | — |
| 未分配利润 | `retained_earnings` | `Decimal` | `未分配利润` | 留存收益 |
| **所有者权益合计** | `total_equity` | `Decimal` | `所有者权益合计` | 股东权益, 净资产 |

---

## 二、利润表 (Income Statement)

| 中文 | 英文变量名 | 类型 | AKShare 原始列名 | 模糊检索别名 |
|------|-----------|------|------------------|-------------|
| **营业总收入** | `total_revenue` | `Decimal` | `营业总收入` | 营收, 总收入, 销售收入 |
| 营业收入 | `operating_revenue` | `Decimal` | `营业收入` | 主营收入 |
| **营业总成本** | `total_operating_cost` | `Decimal` | `营业总成本` | 总成本 |
| 营业成本 | `cost_of_goods_sold` | `Decimal` | `营业成本` | COGS, 主营成本 |
| 销售费用 | `selling_expenses` | `Decimal` | `销售费用` | 营销费用 |
| 管理费用 | `admin_expenses` | `Decimal` | `管理费用` | 行政费用 |
| 研发费用 | `rd_expenses` | `Decimal` | `研发费用` | R&D |
| 财务费用 | `finance_expenses` | `Decimal` | `财务费用` | 利息费用 |
| 资产减值损失 | `asset_impairment_loss` | `Decimal` | `资产减值损失` | 减值 |
| 投资收益 | `investment_income` | `Decimal` | `投资收益` | — |
| **营业利润** | `operating_profit` | `Decimal` | `营业利润` | 经营利润 |
| 营业外收入 | `non_operating_income` | `Decimal` | `营业外收入` | — |
| 营业外支出 | `non_operating_expenses` | `Decimal` | `营业外支出` | — |
| **利润总额** | `total_profit` | `Decimal` | `利润总额` | 税前利润 |
| 所得税费用 | `income_tax_expense` | `Decimal` | `所得税费用` | 所得税 |
| **净利润** | `net_income` | `Decimal` | `净利润` | 纯利润, 纯利 |
| 每股收益(基本) | `basic_eps` | `Decimal` | `基本每股收益` | EPS |

---

## 三、现金流量表 (Cash Flow Statement)

| 中文 | 英文变量名 | 类型 | AKShare 原始列名 | 模糊检索别名 |
|------|-----------|------|------------------|-------------|
| 销售商品收到的现金 | `cash_from_sales` | `Decimal` | `销售商品、提供劳务收到的现金` | — |
| 收到的税费返还 | `tax_refunds_received` | `Decimal` | `收到的税费返还` | — |
| 购买商品支付的现金 | `cash_paid_for_goods` | `Decimal` | `购买商品、接受劳务支付的现金` | — |
| 支付给职工的现金 | `cash_paid_to_employees` | `Decimal` | `支付给职工以及为职工支付的现金` | — |
| **经营活动现金流量净额** | `operating_cashflow` | `Decimal` | `经营活动产生的现金流量净额` | 经营现金流, OCF |
| 购建固定资产支付的现金 | `cash_paid_for_assets` | `Decimal` | `购建固定资产、无形资产和其他长期资产支付的现金` | 资本支出, CapEx |
| 取得投资收益收到的现金 | `cash_from_investment_income` | `Decimal` | `取得投资收益收到的现金` | — |
| **投资活动现金流量净额** | `investing_cashflow` | `Decimal` | `投资活动产生的现金流量净额` | 投资现金流 |
| 吸收投资收到的现金 | `cash_from_investors` | `Decimal` | `吸收投资收到的现金` | — |
| 取得借款收到的现金 | `cash_from_borrowings` | `Decimal` | `取得借款收到的现金` | — |
| 偿还债务支付的现金 | `cash_paid_for_debts` | `Decimal` | `偿还债务支付的现金` | — |
| 分配股利支付的现金 | `cash_paid_for_dividends` | `Decimal` | `分配股利、利润或偿付利息支付的现金` | — |
| **筹资活动现金流量净额** | `financing_cashflow` | `Decimal` | `筹资活动产生的现金流量净额` | 融资现金流 |
| **现金净增加额** | `net_cashflow` | `Decimal` | `现金及现金等价物净增加额` | 现金变动 |

---

## 四、财务比率 (Financial Ratios)

### 盈利能力

| 中文 | 英文变量名 | 类型 | 公式 | 模糊检索别名 |
|------|-----------|------|------|-------------|
| 净资产收益率 | `roe` | `Decimal` | 净利润 / 股东权益 | ROE, return_on_equity |
| 总资产收益率 | `roa` | `Decimal` | 净利润 / 总资产 | ROA, return_on_assets |
| 销售净利率 | `net_profit_margin` | `Decimal` | 净利润 / 营业总收入 | 净利润率, 净利率 |
| 销售毛利率 | `gross_profit_margin` | `Decimal` | (营收-营业成本) / 营收 | 毛利率 |
| 营业利润率 | `operating_profit_margin` | `Decimal` | 营业利润 / 营业总收入 | — |

### 偿债能力

| 中文 | 英文变量名 | 类型 | 公式 | 模糊检索别名 |
|------|-----------|------|------|-------------|
| 流动比率 | `current_ratio` | `Decimal` | 流动资产 / 流动负债 | — |
| 速动比率 | `quick_ratio` | `Decimal` | (流动资产-存货) / 流动负债 | — |
| 资产负债率 | `debt_to_asset_ratio` | `Decimal` | 总负债 / 总资产 | 负债率 |
| 产权比率 | `equity_ratio` | `Decimal` | 总负债 / 股东权益 | 债务权益比 |
| 利息保障倍数 | `interest_coverage` | `Decimal` | 利润总额 / 财务费用 | — |

### 运营效率

| 中文 | 英文变量名 | 类型 | 公式 | 模糊检索别名 |
|------|-----------|------|------|-------------|
| 应收账款周转率 | `receivables_turnover` | `Decimal` | 营收 / 平均应收 | — |
| 存货周转率 | `inventory_turnover` | `Decimal` | 营业成本 / 平均存货 | — |
| 总资产周转率 | `total_asset_turnover` | `Decimal` | 营收 / 平均总资产 | 资产周转率 |

### 估值指标

| 中文 | 英文变量名 | 类型 | 公式 | 模糊检索别名 |
|------|-----------|------|------|-------------|
| 市盈率 | `pe_ratio` | `float` | 股价 / EPS | PE, P/E |
| 市净率 | `pb_ratio` | `float` | 股价 / 每股净资产 | PB, P/B |
| 市销率 | `ps_ratio` | `float` | 总市值 / 营收 | PS, P/S |

---

## 五、分析模型

| 中文 | 英文变量名 | 类型 | 说明 |
|------|-----------|------|------|
| 杜邦分析结果 | `dupont_result` | `DuPontResult` | 杜邦三因素分解 |
| 趋势分析结果 | `trend_result` | `TrendResult` | 多期同比/环比 |
| 同比增长率 | `yoy_growth` | `Decimal` | Year-over-Year |
| 环比增长率 | `qoq_growth` | `Decimal` | Quarter-over-Quarter |
| 自由现金流 | `free_cash_flow` | `Decimal` | FCF = OCF - CapEx |
| AI 分析报告 | `ai_report` | `AnalysisReport` | DeepSeek 生成 |

---

## 六、行情数据

| 中文 | 英文变量名 | 类型 | AKShare 原始列名 | 模糊检索别名 |
|------|-----------|------|------------------|-------------|
| 最新价 | `current_price` | `float` | `最新价` | 股价, 现价 |
| 总市值 | `market_cap` | `Decimal` | `总市值` | — |
| 流通市值 | `float_market_cap` | `Decimal` | `流通市值` | — |
| 成交量 | `volume` | `int` | `成交量` | — |
| 成交额 | `turnover_amount` | `Decimal` | `成交额` | — |
| 涨跌幅 | `price_change_pct` | `float` | `涨跌幅` | — |
| 换手率 | `turnover_rate` | `float` | `换手率` | — |

---

## 七、系统/配置

| 中文 | 英文变量名 | 类型 | 说明 |
|------|-----------|------|------|
| 股票代码 | `stock_code` | `str` | 6位数字，如 "600519" |
| 股票名称 | `stock_name` | `str` | 如 "贵州茅台" |
| 报告期 | `report_date` | `date` | 如 2024-12-31 |
| 分析深度 | `analysis_depth` | `str` | "basic" / "detailed" / "ai_enhanced" |
| 缓存键 | `cache_key` | `str` | Redis 缓存的键名 |
| 缓存过期时间 | `cache_ttl` | `int` | 秒 |

---

## ⚠️ 命名注意事项

1. **金额字段一律 `Decimal`**，比率字段也用 `Decimal`（仅估值 PE/PB/PS 因来源为实时行情，可用 `float`）
2. **Python 后端**用 `snake_case`，**React 前端**用 `camelCase`（如 `totalAssets`）
3. **AKShare 返回的是中文列名**，需经过 `DataTransformer.chinese_to_english()` 转换
4. **模糊检索别名**：用于 `naming_mapper.py`，支持用户输入"净利润率"也能匹配到 `net_profit_margin`
