# 后端接口文档

更新时间：2026-03-31

本文档面向后端、前端和测试同学，描述当前仓库里“可用且已被测试覆盖”的接口契约。项目现在同时保留两套接口：

- `v1`：历史兼容接口，直接围绕股票分析能力输出
- `v2`：archive-first 工作台接口，优先给新前端使用

## 1. 通用约定

- Base URL：`http://{host}:{port}`
- 默认返回：`application/json`
- 鉴权：当前无鉴权
- 时间格式：优先使用 ISO8601 或 `YYYY-MM-DD`
- 主要错误码：
  - `400`：参数非法
  - `404`：股票、报表、归档工作区不存在
  - `500`：内部错误或外部依赖异常

## 2. 服务健康接口

### `GET /`

用途：API 根入口。

返回示例：

```json
{
  "message": "Financial Report Analyzer API",
  "version": "0.2.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

### `GET /health`

用途：健康检查。

返回示例：

```json
{
  "status": "healthy",
  "service": "financial-report-analyzer"
}
```

## 3. v1 兼容接口

这些接口仍然可用，但新页面不建议继续扩展在这套路径上。

### `GET /api/stocks/`

用途：获取股票列表。

查询参数：

- `market`：可选，市场过滤

数据来源：

- `CrawlerService.fetch_stock_list()`
- 默认 provider 取决于 `settings.financial_provider`

### `GET /api/stocks/{code}/statements`

用途：获取指定股票最新一期三张报表。

返回字段：

- `stock_code`
- `balance_sheet`
- `income_statement`
- `cashflow_statement`

### `GET /api/stocks/{code}/ratios`

用途：计算盈利能力、偿债能力、效率指标。

返回字段：

- `stock_code`
- `report_date`
- `profitability`
- `solvency`
- `efficiency`

### `GET /api/stocks/{code}/dupont`

用途：杜邦分析。

响应模型：

- `DuPontResult`

### `GET /api/stocks/{code}/cashflow`

用途：现金流质量分析。

响应模型：

- `CashFlowResult`

### `GET /api/stocks/{code}/trend`

用途：按指标做趋势分析。

查询参数：

- `metric`：默认 `net_income`

### `POST /api/stocks/{code}/ai-report`

用途：生成旧版 AI 分析报告。

说明：

- 依赖 `DeepSeek API`
- 无 `DEEPSEEK_API_KEY` 时会失败

### `GET /api/stocks/{code}/export/excel`

用途：导出 Excel 报告。

返回：

- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

## 4. v2 工作台接口

这套接口是当前 archive-first 前后端契约的核心。

### 4.1 工作区总览

### `GET /api/v2/workspaces`

用途：列出本地 archive-backed 工作区。

查询参数：

- `limit`：默认 `20`，最大 `200`

数据来源：

- `WorkspaceRepository.list_workspaces()`

返回关键字段：

- `stock_code`
- `stock_name`
- `market`
- `latest_report_date`
- `dataset_count`
- `archives`

### `GET /api/v2/workspaces/{code}/metrics`

用途：返回原始指标包，兼容旧测试和内部调试。

返回关键字段：

- `stock_code`
- `stock_name`
- `report_date`
- `catalog`
- `values`
- `summary`

### `GET /api/v2/workspaces/{code}/context`

用途：返回 prompt context builder 的旧版上下文结构。

查询参数：

- `profile_key`：默认 `archive_review`

返回关键字段：

- `profile_key`
- `profile_name`
- `system_prompt`
- `context_text`
- `injection_bundle`

### 4.2 工作区详情

### `GET /api/v2/workspace/{code}/snapshot`

用途：返回工作区快照。

查询参数：

- `lang`：可选，`zh`/`en`/`zh-CN`/`en-US`

返回关键字段：

- `stock`
- `available_periods`
- `statements`
- `source`
- `updated_at`

### `GET /api/v2/workspace/{code}/metrics/catalog`

用途：返回指标目录定义。

查询参数：

- `lang`：可选

返回关键字段：

- `stock_code`
- `stock_name`
- `report_date`
- `total`
- `items`

### `GET /api/v2/workspace/{code}/metrics`

用途：返回分组指标值。

查询参数：

- `lang`：可选

返回关键字段：

- `categories`
- `summary`

### `GET /api/v2/workspace/{code}/models`

用途：返回固定分析模型卡片。

查询参数：

- `lang`：可选

返回关键字段：

- `items[].key`
- `items[].label`
- `items[].verdict`
- `items[].summary`
- `items[].evidence_keys`

### `GET /api/v2/workspace/{code}/insights/context`

用途：返回 AI 洞察上下文。

查询参数：

- `lang`：可选

返回关键字段：

- `profile`
- `injection_bundle.system_prompt`
- `injection_bundle.company_context`
- `injection_bundle.risk_overlay`
- `injection_bundle.model_summary`
- `injection_bundle.metric_digest`

### `GET /api/v2/workspace/{code}/statements`

用途：返回报表详情页所需数据。

查询参数：

- `period`：可选，指定报表期
- `lang`：可选

当前实现说明：

- 同时返回 `tabs` 和 `statements`
- `tabs` 供新的明细页/测试用
- `statements`、`balance_sheet`、`income_statement`、`cashflow_statement` 用于兼容现有前端读取逻辑

返回关键字段：

- `stock`
- `lang`
- `available_periods`
- `selected_period`
- `tabs`
- `statements`
- `updated_at`

### `POST /api/v2/workspace/{code}/insights/generate`

用途：生成工作区 AI 洞察报告。

请求体：

```json
{
  "period": "2025-09-30",
  "lang": "en"
}
```

当前实现说明：

- 正常情况：调用 `WorkspaceService.generate_insight_report()`
- 若未配置 `DEEPSEEK_API_KEY` 或 LLM 调用失败：自动降级为 archive-based 结构化摘要，保证接口仍可用
- 返回中同时保留了新字段和旧字段，便于兼容现有前端

返回关键字段：

- 新字段：
  - `summary`
  - `highlights`
  - `risks`
  - `open_questions`
  - `actions`
  - `evidence`
  - `generated_at`
  - `model_version`
- 兼容字段：
  - `executive_summary`
  - `strengths`
  - `weaknesses`
  - `recommendations`
  - `risk_warnings`

### 4.3 Crawler / 刷新接口

### `GET /api/v2/stocks`

用途：获取股票列表，优先使用本地 workspace 汇总，必要时回源 provider。

查询参数：

- `market`：可选
- `refresh`：可选，默认 `false`

### `GET /api/v2/stocks/{code}/snapshot`

用途：从 provider 获取股票财务快照。

查询参数：

- `latest_only`：默认 `true`
- `refresh`：默认 `false`

### `GET /api/v2/crawler/archives`

用途：查看本地归档列表。

查询参数：

- `stock_code`
- `dataset`
- `limit`

### `POST /api/v2/crawler/jobs`

用途：创建刷新任务。

行为：

- 若 `rq/redis` 可用：走队列
- 不可用：自动降级为同步刷新

### `GET /api/v2/crawler/jobs/{job_id}`

用途：查询刷新任务状态。

## 5. 错误排查建议

### `404 No archived workspace found`

说明本地 `data/raw/baidu_finance/...` 下没有对应股票归档。先执行：

1. `POST /api/v2/crawler/jobs`
2. 再轮询 `GET /api/v2/crawler/jobs/{job_id}`

### `500 DEEPSEEK_API_KEY is not configured`

旧版 `/api/stocks/{code}/ai-report` 会直接失败。

新版 `/api/v2/workspace/{code}/insights/generate` 已做降级，不会因为 key 缺失导致整个页面不可用。

### `500 Unsupported dataset`

检查 `dataset` 是否在以下枚举中：

- `income_statement`
- `balance_sheet`
- `cashflow_statement`
- `financial_indicators`
