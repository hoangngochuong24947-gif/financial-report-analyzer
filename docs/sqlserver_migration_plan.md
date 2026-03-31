# SQL Server 引入方案

更新时间：2026-03-31

本文档讨论“如果后续要把数据库能力真正引入项目，并且目标数据库是 SQL Server，应该怎么做”。

结论先说：

- 现在就能接 SQL Server，但不建议直接把现有文件归档链路硬替换掉
- 更合理的做法是先把数据库定位为“工作区索引 + 作业状态 + 元数据仓库”
- 等数据库抽象层稳定后，再决定是否把部分分析结果物化入库

## 1. 当前状态评估

当前仓库的数据库状态是“配置先行、业务未落地”：

- `pyproject.toml` 已有 `sqlalchemy` 和 `mysql-connector-python`
- `src/config/settings.py` 里已有 `mysql_*` 配置和 `mysql_url`
- 但业务主链没有真正使用 SQLAlchemy engine / session / model
- `storage/` 当前核心是文件系统 archive，不是关系型数据库

这意味着 SQL Server 改造不是“把 MySQL ORM 改方言”，而是：

1. 先补数据库访问抽象
2. 再选定哪些数据值得入库
3. 最后选择 SQL Server 方言与部署方式

## 2. 建议目标架构

推荐分三层：

### 第一层：Archive 仍然是事实源

保留：

- `data/raw/baidu_finance/...`
- `data/processed/baidu_finance/...`

原因：

- 原始 JSON/CSV 适合追溯
- 便于重新解析、重算指标
- 不依赖数据库迁移即可恢复数据

### 第二层：SQL Server 作为索引与业务状态库

第一阶段建议入库的数据：

- 归档清单索引
- 股票基础信息
- 工作区摘要
- crawler job 状态
- AI 报告元数据

第二阶段再考虑入库的数据：

- 标准化后的三张报表
- 指标快照
- 模型卡片
- AI 洞察报告正文

### 第三层：Service 层统一读取策略

建议实现为：

- `ArchiveRepository`：读写文件
- `WorkspaceRepository`：从 archive 聚合工作区
- `DatabaseRepository`：读写数据库元数据
- `WorkspaceService`：根据场景决定读 archive 还是读数据库缓存

## 3. 技术选型建议

## 3.1 SQLAlchemy 方言

推荐使用：

- `mssql+pyodbc`

推荐理由：

- SQLAlchemy 官方生态成熟
- Windows 环境兼容性好
- 企业内网最常见

建议依赖：

```toml
pyodbc = "^5.1.0"
```

连接串示例：

```python
mssql+pyodbc://username:password@host:1433/database?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

如果是 Windows 集成认证，可再单独设计：

```python
mssql+pyodbc://@host:1433/database?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes
```

## 3.2 配置层改造建议

不要继续把数据库配置写死成 `mysql_*`。建议抽象成：

- `db_dialect`
- `db_driver`
- `db_host`
- `db_port`
- `db_user`
- `db_password`
- `db_name`
- `db_query`

示例：

```python
db_dialect: str = "mssql"
db_driver: str = "pyodbc"
db_host: str = "localhost"
db_port: int = 1433
db_user: str = "sa"
db_password: str = ""
db_name: str = "financial_analyzer"
db_odbc_driver: str = "ODBC Driver 18 for SQL Server"
db_trust_server_certificate: bool = True
```

然后统一由一个 `database_url` 属性生成 URL，取代当前 `mysql_url`。

## 3.3 ORM 与迁移工具

建议新增：

- `src/storage/db/engine.py`
- `src/storage/db/session.py`
- `src/storage/db/models.py`
- `alembic/`

推荐迁移工具：

- `Alembic`

原因：

- SQLAlchemy 官方体系
- 后续无论 MySQL 还是 SQL Server 都更易维护

## 4. 分阶段实施方案

## Phase 0：抽象准备

目标：不接 SQL Server，也先把代码结构准备好。

任务：

1. 把 `mysql_*` 配置改成通用 `db_*`
2. 新增 `database_url` 统一构造逻辑
3. 建立 `db/engine.py`、`db/session.py`
4. 明确 repository 边界，不让 API 直接碰 ORM

完成标准：

- 不影响现有 73 个测试
- 默认不开数据库也能正常运行

## Phase 1：只存元数据，不存三表明细

目标：低风险引入 SQL Server。

建议建表：

- `stocks`
- `archive_manifests`
- `workspace_summaries`
- `crawler_jobs`
- `insight_reports`

优点：

- 不改变 archive-first 主链
- 查询工作区列表、归档索引、作业状态会更快
- 为后续后台管理页做准备

落地方式：

1. `ArchiveRepository.save_dataset()` 保存文件后，顺便 upsert 一条 manifest 记录
2. `WorkspaceRepository.list_workspaces()` 优先从数据库读摘要，必要时回退文件系统
3. job 状态写数据库，替代纯内存/纯 RQ 依赖

## Phase 2：把标准化报表入库

目标：让数据库支持检索、筛选、统计和横向对比。

建议建表：

- `financial_balance_sheets`
- `financial_income_statements`
- `financial_cashflow_statements`
- `financial_indicator_snapshots`

建议原则：

- 表字段使用英文稳定键，不存中文列名
- `report_date`、`stock_code`、`dataset_version` 必须建索引
- Decimal 字段使用 SQL Server `DECIMAL(p, s)`，不要用 `FLOAT`

字段类型建议：

- 金额：`DECIMAL(20, 2)`
- 比率：`DECIMAL(12, 6)`
- 日期：`DATE`
- 抓取时间：`DATETIME2`
- JSON 扩展字段：可放 `NVARCHAR(MAX)`，必要时再做 JSON 列策略

## Phase 3：分析结果物化

目标：减少重复计算，支持 BI 和历史回溯。

可入库对象：

- metric bundle
- model cards
- AI 洞察报告

适用场景：

- 查询历史版本
- 对比不同抓取日期的分析结果
- 后台审计和回放

不建议过早做的事：

- 一开始就把所有中间结果都持久化
- 在 archive、ORM、API 三层同时堆业务逻辑

## 5. 代码改造清单

## 5.1 配置层

需要修改：

- `src/config/settings.py`

建议动作：

1. 保留 `mysql_url` 一段时间做兼容
2. 新增 `database_url`
3. 新增 SQL Server 需要的 ODBC 参数

## 5.2 storage 层

建议新增目录：

```text
src/storage/
  archive_repository.py
  workspace_repository.py
  db/
    engine.py
    session.py
    models.py
    repositories/
      manifest_repository.py
      workspace_summary_repository.py
      crawler_job_repository.py
      insight_report_repository.py
```

## 5.3 service 层

建议新增的服务能力：

- `WorkspaceIndexService`
- `CrawlerJobStore`
- `InsightReportStore`

原则：

- API 依赖 service
- service 依赖 repository
- repository 再依赖 SQLAlchemy session

## 5.4 测试层

建议新增测试：

- `tests/test_db_config.py`
- `tests/test_manifest_repository.py`
- `tests/test_workspace_summary_repository.py`
- `tests/test_sqlserver_integration.py`

建议测试顺序：

1. 单元测试先用 SQLite / mock session 跑 repository 逻辑
2. 真正的 SQL Server 集成测试单独标记 `integration`

## 6. SQL Server 特别注意事项

## 6.1 Decimal 精度

这个项目对 Decimal 很敏感，数据库字段必须与 Python `Decimal` 保持一致。

建议：

- 金额字段：`DECIMAL(20, 2)`
- 比率字段：`DECIMAL(12, 6)` 或更高
- 避免在 ORM 层自动转 float

## 6.2 中文与排序规则

由于项目里有中文股票名和部分中文上下文，建议：

- 字符串字段使用 `NVARCHAR`
- 明确数据库排序规则与字符集

## 6.3 批量写入

财报明细和指标快照如果入库，建议：

- 优先用 bulk insert / executemany
- 控制事务粒度
- 不要在一个股票的每一行上独立 commit

## 6.4 连接池

默认可以先沿用：

- `pool_pre_ping=True`
- `pool_recycle`
- 合理的 `pool_size` / `max_overflow`

但在企业 SQL Server 环境里，真正要关注的是：

- 连接空闲超时
- ODBC Driver 版本
- TLS / 证书策略

## 7. 推荐的最小可落地路线

如果要低风险推进，我建议按下面顺序做：

1. 先把数据库配置抽象成通用 `db_*`
2. 引入 SQLAlchemy engine/session + Alembic
3. 先只落 `archive_manifests`、`crawler_jobs`、`insight_reports`
4. 保持 archive 文件为事实源不变
5. 跑通 SQL Server 集成测试后，再考虑三表和指标入库

这样做的好处：

- 对当前接口影响最小
- 不会破坏 archive-first 设计
- 新能力能逐步上线，不需要一次性大迁移

## 8. 不建议的路线

以下做法不推荐：

- 直接把 `ArchiveRepository` 改成“只写 SQL Server，不写文件”
- 在没有 repository 抽象的前提下，让 API 路由直接写 ORM
- 继续沿用 `mysql_*` 配置名去承载 SQL Server
- 一上来就设计成“所有报表、指标、报告都必须入库才可查询”

## 9. 一句话判断标准

什么时候可以说“SQL Server 接入做好了”？

至少要满足这四条：

1. 关闭数据库时，archive-first 主链仍然可跑
2. 开启数据库时，工作区索引和作业状态能稳定落库
3. 所有 Decimal 字段往返读写不丢精度
4. 有 Alembic 迁移脚本和 SQL Server 集成测试
