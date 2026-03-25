# 前端设计与接口复用方案（含 SDK 自动生成）

更新时间：2026-03-22

## 1. 复用优先，不重复造轮子

### 1.1 项目内已有可复用资产

- 视觉与页面草图：`frontend/DESIGN.md`
- 可运行静态原型：`frontend/index.html`
- 后端接口与分层规划：`docs/architecture_api_frontend_optimization_plan.md`

### 1.2 外部开源优先选型（已核验）

- OpenAPI SDK 生成：[`openapi-typescript`](https://openapi-ts.dev/)（类型）+ [`openapi-fetch`](https://openapi-ts.dev/openapi-fetch/)（轻量客户端）
- 可选增强（后续）：[`orval`](https://orval.dev/)（可直接产出 hooks/mocks）
- 服务端状态管理：[`@tanstack/react-query`](https://tanstack.com/query/latest/docs/framework/react/overview)
- 后台管理模板可借鉴：
  - [`ant-design/ant-design-pro`](https://github.com/ant-design/ant-design-pro)
  - [`refinedev/refine`](https://github.com/refinedev/refine)
  - [`marmelab/react-admin`](https://github.com/marmelab/react-admin)
  - [`tremorlabs/tremor`](https://github.com/tremorlabs/tremor)

## 2. 前端落地架构（建议）

```text
frontend/
  openapi/
    openapi.json                 # 由后端自动导出
  src/
    api/
      generated/
        schema.ts                # 自动生成，禁止手改
      client.ts                  # openapi-fetch 客户端
      sdk.ts                     # 业务封装 API（v2 优先）
      README.md
    vite-env.d.ts
```

## 3. 已落地：OpenAPI 自动生成 SDK

### 3.1 生成链路

1. 后端导出 schema  
`python ../scripts/export_openapi.py --output ./openapi/openapi.json`

2. 前端生成 TS 类型  
`openapi-typescript ./openapi/openapi.json --output ./src/api/generated/schema.ts`

3. 一键执行  
`npm run gen:api`

### 3.2 已新增文件

- `scripts/export_openapi.py`
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/.env.example`
- `frontend/src/vite-env.d.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/sdk.ts`
- `frontend/src/api/README.md`

## 4. 前端接口对接建议（v2 优先）

- 股票列表：`GET /api/v2/stocks`
- 快照查询：`GET /api/v2/stocks/{code}/snapshot`
- 提交刷新任务：`POST /api/v2/crawler/jobs`
- 查询任务状态：`GET /api/v2/crawler/jobs/{job_id}`

建议页面流程：

1. 列表页先拉 `stocks`
2. 详情页拉 `snapshot`
3. 点击“刷新数据”创建 job
4. 轮询 job 状态到 `finished`

## 5. 你需要提供给后端的 API/鉴权信息（模板）

如果你准备接入新的数据源（非 AKShare），请一次性给出：

1. 供应商名称与文档链接
2. Base URL 与环境（prod/sandbox）
3. 鉴权方式（API Key / Bearer Token / Cookie / 签名）
4. 需要的 Header / Query / Body 字段
5. 限频规则（QPS、日调用上限）
6. 错误码与重试建议
7. 一个真实请求与响应样例

## 6. 当前项目是否需要 cookie/token

- 抓取 A 股基础财务（AKShare）：通常不需要 cookie/token
- AI 报告：需要 `DEEPSEEK_API_KEY`
- 异步任务：推荐启用 Redis（无 token，按内网部署）

## 7. 后续建议（按优先级）

1. 引入 React Query（缓存、重试、轮询统一）
2. 评估 Orval（如果你希望自动产出 hooks）
3. 增加 MSW 契约 Mock（前后端并行开发）
