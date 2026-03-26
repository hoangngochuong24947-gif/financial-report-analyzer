# 百度股市通存储规划

## 目录结构
```text
data/
  raw/
    baidu_finance/
      {stock_code}/
        {dataset}/
          {fetch_date}/
            *.json
        manifests/
          manifest_*.json
  processed/
    baidu_finance/
      {stock_code}/
        {dataset}/
          *.csv
```

## 命名规则
- 原始 JSON: `{stock_code}_{dataset}_{request_group}_{fetch_ts}.json`
- 处理后 CSV: `{stock_code}_{dataset}_{period_start}_{period_end}.csv`
- manifest: `manifest_{stock_code}_{fetch_ts}_{dataset}.json`

## Manifest Schema
- `stock_code`
- `stock_name`
- `market`
- `dataset`
- `entry_url`
- `entry_params`
- `request_url`
- `request_params`
- `raw_path`
- `csv_path`
- `manifest_path`
- `row_count`
- `fetched_at`
- `status`
- `error`

## 原始层与处理层职责
- 原始层: 保留上游真实响应，便于重放、排错、补解析。
- 处理层: 为分析、导表、数据库导入提供稳定二维结构。
- manifest: 作为一次抓取的事实索引，连接原始层与处理层。

## CSV 字段组织
- 三大表 CSV:
  - `report_label`
  - `report_date`
  - 其余列为百度原始中文科目名
- 指标 CSV:
  - `metric`
  - `latest_report_label`
  - `latest_value`
  - `values`

## 入库映射建议
- 数据库导入阶段不直接读取页面，而读取 manifest 驱动的 CSV/JSON。
- 三大表可映射到标准财务事实表。
- 指标可映射到宽表或 key-value 明细表。
- 建议保留 `provider`、`source_manifest_path`、`fetched_at` 作为审计字段。
