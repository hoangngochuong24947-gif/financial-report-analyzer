# 百度股市通接口规划

## 固定入口接口
- URL: `https://finance.pae.baidu.com/api/stockwidget`
- 作用: 作为财务页入口和页面初始化数据来源。
- 核心参数:
  - `code`
  - `market=ab`
  - `type=stock`
  - `widgetType=finance`
  - `finClientType=pc`

## 子接口发现机制
- 用 Playwright 打开 `https://gushitong.baidu.com/stock/ab-{code}?mainTab=财务`。
- 监听页面网络请求。
- 点击财务页不同 tab，捕获真实 `selfselect/openapi` 和 `opendata` 请求。
- 发现成功后，将 URL 和 params 交给 HTTP 客户端回放。

## 已知映射
- `income_statement` -> `group=income_detail`
- `balance_sheet` -> `group=balance_detail`
- `cashflow_statement` -> `group=cash_flow_detail`
- `financial_indicators` -> 页面 tab `关键指标`，当前以 DOM 抓取为主，发现到的 `opendata` 结果仅作记录

## Headers 策略
- 使用桌面浏览器 User-Agent。
- 保持 `Referer` 为 `https://gushitong.baidu.com/`。
- 使用 `curl_cffi` 模拟浏览器 TLS/HTTP 行为，降低被风控概率。

## 反爬与稳定性注意事项
- 页面接口依赖前端上下文，单纯猜参数容易失效，优先走发现层。
- 指标页 `opendata` 当前可能返回空结果，因此保留 DOM 抓取兜底。
- 请求频率需可配置，避免高并发。
- 一旦页面文案或 tab 名称变化，优先排查 discovery 和 DOM 抓取逻辑。

## 响应结构样例
- 三大表接口核心结构:
  - `Result.info`
  - `Result.data[].text`
  - `Result.data[].content[].data[].header/body`
- 指标抓取结果结构:
  - `rows[].metric`
  - `rows[].latest_report_label`
  - `rows[].latest_value`
  - `latest`

## 字段提取规则
- 报告期从 `2024年报`、`2024中报`、`2024三季报`、`2024一季报` 解析。
- 报表字段靠中文别名映射到项目模型字段。
- 指标快照优先取每个指标的最新值。

## 接口漂移排查流程
1. 先确认入口 `stockwidget` 是否还能正常返回。
2. 用浏览器重放财务页，确认 tab 点击是否仍触发网络请求。
3. 比对 `group`、`query`、`tag` 是否变化。
4. 若子接口还能返回但结构变化，更新 `extractors.py` 和 `parsers.py`。
5. 若接口失效，临时回退到 DOM 抓取或 AKShare 指标兜底。
