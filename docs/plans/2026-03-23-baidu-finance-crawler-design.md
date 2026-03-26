# 百度股市通财务爬虫设计

## 目标与范围
- 首版数据源为百度股市通财务页。
- 首版数据集仅覆盖 `income_statement`、`balance_sheet`、`cashflow_statement`、`financial_indicators`。
- 首版持久化仅做原始 JSON 归档、处理后 CSV 和 manifest，不直接入 MySQL。

## 完成定义
- 能按股票代码抓取三大表和关键指标。
- 能将原始请求响应、处理后 CSV、manifest 落盘到统一目录。
- 能通过统一 `FinancialDataGateway` 暴露给现有分析和 API 层。
- 能通过文档让后续开发者继续接入东方财富、数据库和批量调度。

## 数据流
1. 访问 `stockwidget` 入口接口。
2. 通过浏览器发现财务页子请求参数。
3. 用 `curl_cffi` 回放三大表接口。
4. 用 Playwright 抓取关键指标表格文本。
5. 解析成现有 `BalanceSheet`、`IncomeStatement`、`CashFlowStatement`。
6. 原始 JSON、CSV、manifest 归档。
7. 通过 `BaiduFinanceProvider` 提供统一输出。

## 模块边界
- `client.py`: HTTP 请求、超时、重试、Headers。
- `discovery.py`: 打开百度页面并发现异步接口参数。
- `endpoint_registry.py`: 数据集与 tab、group、query 的静态映射。
- `extractors.py`: 扁平化响应、生成 CSV 行、提取指标快照。
- `parsers.py`: 转换为项目现有财务模型。
- `service.py`: 编排完整抓取与归档流程。
- `archive_repository.py`: 文件系统落盘与归档查询。
- `baidu_finance_provider.py`: 对接 `FinancialDataGateway`。

## Provider 抽象
- `FinancialDataGateway` 继续作为统一入口。
- 标准化方法职责：返回分析层可直接使用的财务模型。
- 原始归档职责：返回原始 JSON、CSV、manifest 的路径和元信息。
- `CrawlerService` 根据 `financial_provider` 选择 `AKShareProvider` 或 `BaiduFinanceProvider`。

## 存储与命名
- 原始目录：`data/raw/baidu_finance/{stock_code}/{dataset}/{fetch_date}/`
- 处理目录：`data/processed/baidu_finance/{stock_code}/{dataset}/`
- manifest 目录：`data/raw/baidu_finance/{stock_code}/manifests/`
- 原始 JSON：`{stock_code}_{dataset}_{request_group}_{fetch_ts}.json`
- 处理 CSV：`{stock_code}_{dataset}_{period_start}_{period_end}.csv`
- manifest：`manifest_{stock_code}_{fetch_ts}_{dataset}.json`

## 配置项
- `financial_provider`
- `archive_root`
- `baidu_finance_timeout`
- `baidu_finance_retry_count`
- `baidu_finance_user_agent`

## 错误处理
- 入口发现失败：记录日志并终止该股票抓取。
- 三大表接口失败：保留原始错误，manifest 标记失败。
- 关键指标抓取失败：优先记录百度 DOM 抓取失败，再回退到 AKShare 指标。
- 文件写入失败：抛出异常，由上层 API 或脚本捕获。

## 测试策略
- 单元测试：解析器、CSV 行构造、文件命名、manifest 生成。
- 集成测试：单股票完整抓取、provider 切换、归档查询接口。
- 文档验收：仅看文档即可完成新增 provider 和新增存储层设计。

## 后续扩展
- 新增东方财富 provider，与百度 provider 同级。
- 新增 repository 层，将 JSON/CSV 导入 MySQL。
- 新增批量调度、增量更新、失败重试。
- 新增多源比对和响应 schema 漂移检测。
