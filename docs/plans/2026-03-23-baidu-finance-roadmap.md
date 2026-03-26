# 百度股市通扩展路线

## 1. 东方财富 Provider
- 与 `BaiduFinanceProvider` 同级实现 `FinancialDataGateway`。
- 复用 `ArchiveRepository`、`Dataset`、manifest schema。
- 解析输出继续对齐现有财务模型，避免分析层改造。

## 2. MySQL Repository
- 增加 `repository` 层负责 CSV/JSON 导入。
- 文件归档继续保留，数据库只做二级存储和查询加速。
- manifest 作为导入任务的事实来源。

## 3. 批量调度
- 复用现有 job/queue 体系。
- 支持股票池抓取、按报告期增量更新、失败自动重试。
- 加上 provider 维度，支持按数据源分批抓取。

## 4. 多源比对
- 同一股票同一报告期对比百度、东方财富、AKShare 结果。
- 输出字段覆盖率、数值差异、缺失情况。
- 为数据质量告警提供依据。

## 5. API 产品化
- `crawl once`
- `list archives`
- `load latest dataset`
- `compare providers`
- `reparse from raw payload`

## 6. 风险与优先级
- P0: 接口发现和归档稳定。
- P1: 东方财富接入与批量调度。
- P2: 数据库入库和多源比对。
- P3: 漂移检测、字段覆盖率统计和告警。

## 7. 推荐开发顺序
1. 先稳定百度抓取与归档。
2. 再做归档查询 API。
3. 然后做数据库导入。
4. 再接东方财富。
5. 最后补多源比对和治理能力。
