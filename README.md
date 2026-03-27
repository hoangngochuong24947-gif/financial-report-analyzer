# Financial Report Analyzer

基于百度股市通归档数据的 A 股财报分析工作台。

这个仓库现在已经从“直接依赖在线接口的分析脚本”重构为“archive-first 的前后端项目”：

- 后端以百度股市通爬虫产出的 JSON/CSV/manifest 归档为主数据源
- 在线抓取只负责刷新和补档，不再作为主分析链路的唯一依赖
- 前端提供三页工作台：指标页、模型页、AI 洞察页
- AKShare 仍保留在项目里，但当前主财务口径已经切到百度归档优先

## 当前状态

- 已有 archive-first workspace API
- 已有 20+ 核心财务指标目录和分组输出
- 已有 5 个固定财务分析模型卡片
- 已有 AI 提示词注入上下文接口
- 已有 Anthropic 风格三页前端骨架

当前更接近“第一阶段可联调版本”，不是最终形态。AI 结论页现在优先展示结构化 prompt injection bundle，而不是完整自动报告编排。

## 技术栈

### 后端

- FastAPI
- Python 3.10+
- pydantic v2
- pandas / NumPy
- Loguru
- MySQL / Redis（可选）
- Poetry

### 数据

- 百度股市通归档数据
- 本地归档结构：`data/raw/baidu_finance` 与 `data/processed/baidu_finance`
- AKShare 保留为非关键回退能力

### 前端

- React 18
- Vite
- TypeScript
- TanStack Query
- openapi-fetch

## 项目结构

```text
src/
├── analyzer/                 # 指标引擎、模型引擎、杜邦/现金流/趋势分析
├── api/                      # FastAPI 路由与 workspace service
├── crawler/                  # 百度股市通抓取、归档、任务队列
├── llm_engine/               # prompt profile、context builder、报告生成
├── models/                   # pydantic 数据模型
├── storage/                  # archive repository、workspace repository
└── utils/                    # 精度、日志、字段映射

frontend/
├── src/api/                  # 前端 API 客户端
├── src/components/           # 工作台组件
├── src/pages/                # Metrics / Models / Insights 三页
└── src/lib/                  # 前端工具函数与路由状态
```

## 核心架构

### 1. 数据分层

- `raw archive`
  - 保存百度原始 JSON、manifest、抓取元数据
- `normalized snapshot`
  - 将三大报表解析成统一内部模型
- `analysis dataset`
  - 在 snapshot 基础上计算指标、模型结果、AI 上下文

### 2. archive-first 工作流

1. 百度股市通抓取并写入归档
2. `WorkspaceRepository` 从归档读取一个股票工作区
3. `WorkspaceMetricEngine` 计算核心指标
4. `WorkspaceModelEngine` 生成分析模型卡片
5. `WorkspaceService` 统一组装 API 响应
6. 前端三页工作台消费同一套 workspace 契约

## 主要接口

### 工作区接口

- `GET /api/v2/workspaces`
- `GET /api/v2/workspace/{code}/snapshot`
- `GET /api/v2/workspace/{code}/metrics/catalog`
- `GET /api/v2/workspace/{code}/metrics`
- `GET /api/v2/workspace/{code}/models`
- `GET /api/v2/workspace/{code}/insights/context`

### 抓取与刷新接口

- `GET /api/v2/stocks`
- `GET /api/v2/stocks/{code}/snapshot`
- `GET /api/v2/crawler/archives`
- `POST /api/v2/crawler/jobs`
- `GET /api/v2/crawler/jobs/{job_id}`

### 旧接口

仓库中仍保留部分旧版 `/api/stocks/...` 接口，用于兼容历史分析逻辑；新的工作台优先使用 workspace 路由。

## 快速开始

### 1. 安装依赖

这个仓库当前主要以应用方式运行，而不是 Poetry 可安装包方式运行。建议：

```bash
poetry install --no-root
```

前端依赖：

```bash
cd frontend
npm install
```

### 2. 环境变量

复制 `.env.example` 为 `.env`，按需配置：

- MySQL
- Redis
- DeepSeek API Key

如果 Redis 或 MySQL 不可用，部分能力会降级，但 archive-first 的核心链路仍可运行。

### 3. 启动后端

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

文档地址：

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 4. 启动前端

```bash

cd frontend
npm run dev
```

## 测试与验证

### 后端 workspace 相关测试

```bash
poetry run pytest tests/test_workspace_repository.py tests/test_workspace_metrics.py tests/test_prompt_context.py tests/test_workspace_api.py -q
```

### 前端构建验证

```bash
cd frontend
npm run build
```

## 当前已落地的分析能力

### 指标页

- 统一 snapshot 展示
- 20+ 核心指标目录
- 指标按 `profitability / solvency / efficiency / cashflow / trend / capital` 分组

### 模型页

- DuPont Analysis
- Cashflow Quality
- Growth Quality
- Solvency Pressure
- Operating Efficiency

### AI 洞察页

- Prompt profile
- System prompt
- Company context
- Risk overlay
- Metric digest
- Model summary
- Output contract

## 已知边界

- 仍有部分 Pydantic / FastAPI deprecation warnings，当前不阻塞功能
- OpenAPI 生成类型与 workspace 新接口还在继续同步中
- 全量测试未全部重跑时，不应把仓库视为完全稳定版
- AI 页目前重点是“可控注入和证据链”，不是复杂 agent 编排

## 推荐开发顺序

1. 先确认百度归档数据完整
2. 再扩指标字典和多轮计算
3. 再补模型解释层
4. 最后再做 AI 结论生成和提示词策略优化

## License

MIT
