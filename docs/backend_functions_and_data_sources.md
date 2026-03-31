# 后端函数、模块与数据源说明

更新时间：2026-03-31

本文档说明“核心模块负责什么、主要函数怎么串起来、真实数据从哪里来”，方便新开发者快速建立心智模型。

## 1. 当前真实数据链路

项目虽然还保留了 AKShare、MySQL、Redis、DeepSeek 等依赖配置，但 2026-03-31 代码里的主链路已经明显转向：

`Baidu Finance 归档 -> WorkspaceRepository -> WorkspaceMetricEngine / WorkspaceModelEngine -> WorkspaceService -> /api/v2/workspace...`

也就是说：

- 工作台主路径：读本地 archive
- 在线刷新：通过 crawler 拉新数据并落到 archive
- AKShare：更多承担 provider / 历史兼容角色
- MySQL：目前配置已在，但不在主业务链路上
- Redis / RQ：任务队列和缓存的可选增强
- DeepSeek：AI 洞察生成的可选增强

## 2. 数据源清单

| 数据源 | 位置/模块 | 当前角色 | 是否关键路径 |
|---|---|---|---|
| 百度股市通归档 | `data/raw/baidu_finance`, `data/processed/baidu_finance` | 主数据源 | 是 |
| 百度股市通在线抓取 | `src/crawler/providers/baidu_finance_*` | 刷新归档、补档 | 是 |
| AKShare | `src/data_fetcher/`, `src/crawler/providers/akshare_provider.py` | 兼容 provider / 老接口数据源 | 否 |
| Redis | `src/data_fetcher/cache_manager.py`, `src/crawler/jobs.py` | 缓存、队列 | 否 |
| RQ | `src/crawler/jobs.py` | 异步刷新任务 | 否 |
| DeepSeek API | `src/llm_engine/llm_client.py` | AI 报告/洞察 | 否 |
| MySQL 配置 | `src/config/settings.py` | 预留数据库配置 | 否 |

## 3. 模块分层与职责

## 3.1 API 层

### `src/main.py`

职责：

- 创建 FastAPI app
- 注册路由
- 注入 CORS 中间件
- 启动/关闭日志

当前注册的路由模块：

- `routes_stock`
- `routes_analysis`
- `routes_report`
- `routes_v2`
- `routes_workspace`

### `src/api/dependencies.py`

职责：

- 提供 `CrawlerService` 单例
- 提供 `WorkspaceService` 单例

关键函数：

- `get_crawler_service()`
- `get_workspace_service()`

### `src/api/routes_stock.py`

职责：

- 暴露 v1 股票列表与三张报表接口

关键函数：

- `get_stock_list()`
- `get_financial_statements()`

### `src/api/routes_analysis.py`

职责：

- 暴露 v1 财务比率、杜邦、现金流、趋势分析接口

关键函数：

- `get_financial_ratios()`
- `get_dupont_analysis()`
- `get_cashflow_analysis()`
- `get_trend_analysis()`

### `src/api/routes_report.py`

职责：

- 暴露 v1 AI 报告与 Excel 导出接口

关键函数：

- `generate_ai_report()`
- `export_excel_report()`

### `src/api/routes_v2.py`

职责：

- 暴露 crawler / stock snapshot 相关 v2 接口
- 更偏向在线抓取与任务控制

关键函数：

- `list_stocks_v2()`
- `get_stock_snapshot_v2()`
- `list_crawler_archives()`
- `create_crawl_job()`
- `get_crawl_job()`

### `src/api/routes_workspace.py`

职责：

- 暴露 archive-first 工作台接口
- 兼容旧测试和当前前端两套返回结构
- 为 AI 洞察提供 LLM 失败降级

关键函数：

- `list_workspaces()`
- `get_workspace_metric_bundle()`
- `get_workspace_context()`
- `get_workspace_snapshot()`
- `get_workspace_metric_catalog()`
- `get_workspace_metric_values()`
- `get_workspace_models()`
- `get_workspace_insight_context()`
- `get_workspace_statements()`
- `generate_workspace_insights()`

### `src/api/workspace_service.py`

职责：

- 工作台的核心组装层
- 负责把 repository、metric engine、model engine、prompt builder 串起来

你可以把它理解为“面向前端契约的应用服务层”。

最重要的方法：

- `list_workspaces()`
- `get_workspace()`
- `get_metric_bundle()`
- `get_context()`
- `get_snapshot_response()`
- `get_statement_detail_response()`
- `get_metric_catalog_response()`
- `get_metric_values_response()`
- `get_model_response()`
- `get_insight_context_response()`
- `generate_insight_report()`

## 3.2 Crawler / Provider 层

### `src/crawler/interfaces.py`

职责：

- 定义 crawler 域异常
- 定义 `Dataset` 枚举
- 定义 `FinancialDataGateway` 协议
- 定义 `FinancialSnapshot`

关键对象：

- `CrawlerDataNotFoundError`
- `CrawlerDependencyError`
- `Dataset`
- `FinancialDataGateway`
- `FinancialSnapshot`

### `src/crawler/service.py`

职责：

- API 侧统一入口，不直接暴露具体 provider
- 根据 `settings.financial_provider` 选择默认 provider

关键函数：

- `fetch_stock_list()`
- `fetch_balance_sheet()`
- `fetch_income_statement()`
- `fetch_cashflow_statement()`
- `fetch_financial_indicators()`
- `get_snapshot()`
- `refresh_snapshot()`
- `list_archives()`
- `to_snapshot_payload()`

### `src/crawler/providers/baidu_finance_provider.py`

职责：

- 对接百度股市通在线抓取能力
- 与 archive-first 路线更一致

适用场景：

- 新数据刷新
- 工作区补档

### `src/crawler/providers/akshare_provider.py`

职责：

- 包装 AKShare 数据访问
- 提供兼容型 provider

适用场景：

- 老接口
- 非 archive-first 回退路径

### `src/crawler/jobs.py`

职责：

- 处理刷新任务
- 有队列时走 RQ；无队列时同步降级

关键函数：

- `enqueue_refresh_snapshot()`
- `enqueue_local_refresh_snapshot()`
- `get_job_status()`
- `has_queue_dependencies()`

## 3.3 Repository / 持久化层

### `src/storage/archive_repository.py`

职责：

- 把原始抓取结果和处理后的 CSV 落到文件系统

关键函数：

- `save_dataset()`
- `list_archives()`

真实目录结构：

- `data/raw/baidu_finance/{stock_code}/{dataset}/{date}/...json`
- `data/raw/baidu_finance/{stock_code}/manifests/...json`
- `data/processed/baidu_finance/{stock_code}/{dataset}/...csv`

### `src/storage/workspace_repository.py`

职责：

- 从 archive 中还原一个“股票工作区”

关键函数：

- `load_workspace()`
- `list_workspaces()`
- `_load_archive_items()`
- `_load_snapshot()`
- `_load_indicator_snapshot()`
- `_read_raw_payload()`

关键输出对象：

- `ArchiveWorkspace`

`ArchiveWorkspace` 包含：

- `stock_code`
- `stock_name`
- `market`
- `snapshot`
- `indicator_snapshot`
- `archives`
- `latest_report_date`

## 3.4 分析层

### `src/analyzer/ratio_calculator.py`

职责：

- 计算盈利、偿债、效率指标

主要函数：

- `calc_profitability()`
- `calc_solvency()`
- `calc_efficiency()`

### `src/analyzer/dupont_analyzer.py`

职责：

- 计算杜邦拆解结果

主要函数：

- `analyze()`

### `src/analyzer/cashflow_analyzer.py`

职责：

- 现金流质量分析

主要函数：

- `analyze()`

### `src/analyzer/trend_analyzer.py`

职责：

- 同比/环比/趋势类计算

主要函数：

- `calc_yoy()`
- `calc_qoq()`
- `analyze_trend()`

### `src/analyzer/metric_engine.py`

职责：

- 基于 `FinancialSnapshot` 生成 archive-first 指标包

主要函数：

- `build_bundle()`
- `grouped_values()`
- `value_map()`

输出：

- `WorkspaceMetricBundle`

### `src/analyzer/model_engine.py`

职责：

- 根据指标值生成固定模型卡片

主要函数：

- `build_items()`
- `_dupont()`
- `_cashflow_quality()`
- `_growth_quality()`
- `_solvency_pressure()`
- `_operating_efficiency()`

输出：

- `AnalysisModelItem[]`

## 3.5 LLM 层

### `src/llm_engine/context_builder.py`

职责：

- 把工作区和指标包拼成 prompt context

主要函数：

- `build()`

输出：

- `AiContextResponse`

### `src/llm_engine/llm_client.py`

职责：

- 封装 DeepSeek chat completion 调用

主要函数：

- `analyze()`
- `get_llm_client()`

注意：

- 没有 `DEEPSEEK_API_KEY` 时会抛 `RuntimeError`

### `src/llm_engine/report_generator.py`

职责：

- 旧版 AI 报告生成逻辑

适用：

- `/api/stocks/{code}/ai-report`

## 3.6 工具层

### `src/utils/precision.py`

职责：

- Decimal 精度控制，是财务计算的底层约束

关键函数：

- `to_amount()`
- `to_ratio()`
- `safe_divide()`

开发约束：

- 货币和比率不要直接用 `float`
- 新增分析逻辑时优先复用这些函数

### `src/utils/naming_mapper.py`

职责：

- 中文字段名与标准英文键之间的映射

用途：

- 解析 AKShare / 百度原始字段
- 给模型和 API 提供稳定字段名

### `src/utils/logger.py`

职责：

- Loguru 初始化与统一日志出口

## 4. 典型调用链

## 4.1 工作台指标页

`GET /api/v2/workspace/{code}/metrics`

调用链：

1. `routes_workspace.get_workspace_metric_values`
2. `WorkspaceService.get_metric_values_response`
3. `WorkspaceService.get_metric_bundle`
4. `WorkspaceRepository.load_workspace`
5. `WorkspaceMetricEngine.build_bundle`

## 4.2 报表详情页

`GET /api/v2/workspace/{code}/statements`

调用链：

1. `routes_workspace.get_workspace_statements`
2. `WorkspaceService.get_statement_detail_response`
3. `WorkspaceRepository.load_workspace`
4. `_statement_rows()` 组装 tabbed rows

## 4.3 AI 洞察页

`POST /api/v2/workspace/{code}/insights/generate`

调用链：

1. `routes_workspace.generate_workspace_insights`
2. `WorkspaceService.generate_insight_report`
3. `WorkspaceService.get_insight_context_response`
4. `WorkspaceService.get_model_response`
5. `get_llm_client().analyze(...)`
6. 失败时降级为 archive summary payload

## 5. 当前值得注意的技术现状

### 5.1 MySQL / SQLAlchemy 还没有进入主业务链路

虽然依赖里有：

- `sqlalchemy`
- `mysql-connector-python`

但当前代码检索结果表明：

- 还没有真正的 ORM model / session / engine 主链
- 配置层仍是 `mysql_*`
- 业务数据主要存文件系统 archive

这意味着：

- 后续接入 SQL Server 的改造空间很大
- 但也说明改造成本更多在“补抽象层”而不是“迁移复杂 ORM 旧债”

### 5.2 archive-first 是目前最重要的设计前提

如果新增功能优先考虑数据库，而忽略 archive 目录这条主链，很容易做出与现有设计不一致的实现。

建议新增能力时优先问三个问题：

1. 这份数据是否已经存在 archive？
2. 这个接口是应该读 archive，还是应该触发在线刷新？
3. 数据库存的是业务状态，还是只是 archive 的索引/缓存？
