# 🐬 MySQL 使用指南 — 从安装后到项目连接

> **适用对象**：已安装 MySQL 但不熟悉操作的开发者  
> **目标**：让你能在本项目中正确使用 MySQL 存储财务数据

---

## 一、确认 MySQL 已正常运行

打开 **PowerShell**，执行：

```powershell
# 检查 MySQL 服务是否在运行
Get-Service -Name "MySQL*"
```

你应该看到 `Status: Running`。如果显示 `Stopped`：

```powershell
# 启动 MySQL 服务
Start-Service -Name "MySQL80"   # 名字可能是 MySQL80 或 MySQL
```

---

## 二、首次登录 MySQL

### 方式 A：命令行登录（推荐）

```powershell
# 如果 MySQL 在系统 PATH 中
mysql -u root -p
# 输入你安装时设置的 root 密码
```

如果提示 `mysql 不是内部或外部命令`，说明 MySQL 没加入 PATH。你需要：

```powershell
# 找到 MySQL 安装路径（一般是以下之一）
# C:\Program Files\MySQL\MySQL Server 8.0\bin\
# C:\Program Files\MySQL\MySQL Server 8.4\bin\

# 用完整路径登录
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

**把 MySQL 加入 PATH（一劳永逸）**：

```powershell
# 管理员模式 PowerShell 执行
[System.Environment]::SetEnvironmentVariable(
    "Path",
    [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";C:\Program Files\MySQL\MySQL Server 8.0\bin",
    "Machine"
)
# 重启 PowerShell 后生效
```

### 方式 B：使用图形界面工具

推荐安装 **MySQL Workbench**（MySQL 官方的图形化管理工具，安装 MySQL 时可能已经随附安装了）。

打开后：

1. 点击 `Local instance MySQL`
2. 输入 root 密码
3. 进入可视化操作界面

---

## 三、为本项目创建数据库和用户

登录 MySQL 后，执行以下 SQL（**直接复制粘贴**）：

```sql
-- ========== 步骤 1：创建数据库 ==========
CREATE DATABASE IF NOT EXISTS financial_analyzer 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- ========== 步骤 2：创建专用用户（不要用 root 连接项目） ==========
CREATE USER IF NOT EXISTS 'fin_user'@'localhost' 
    IDENTIFIED BY 'Fin@2024secure';

-- ========== 步骤 3：给用户授权 ==========
GRANT ALL PRIVILEGES ON financial_analyzer.* TO 'fin_user'@'localhost';
FLUSH PRIVILEGES;

-- ========== 步骤 4：验证 ==========
SHOW DATABASES;
-- 你应该能看到 financial_analyzer
```

> ⚠️ 密码 `Fin@2024secure` 只是示例，**你可以改成自己的密码**，但要同步更新到项目的 `.env` 文件中。

---

## 四、项目中的 `.env` 配置

在项目根目录 `financial-report-analyzer/.env` 文件中填写：

```env
# ===== MySQL 配置 =====
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=fin_user
MYSQL_PASSWORD=Fin@2024secure
MYSQL_DATABASE=financial_analyzer

# ===== Redis 配置 =====
REDIS_HOST=localhost
REDIS_PORT=6379

# ===== DeepSeek LLM 配置 =====
DEEPSEEK_API_KEY=你的DeepSeek-API-Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

---

## 五、Python 连接 MySQL 的方式

本项目使用 **SQLAlchemy**（ORM）+ **aiomysql**（异步驱动）连接 MySQL。

### 连接字符串格式

```python
# 同步连接（开发调试用）
DATABASE_URL = "mysql+pymysql://fin_user:Fin@2024secure@localhost:3306/financial_analyzer"

# 异步连接（FastAPI 推荐，生产用）
DATABASE_URL = "mysql+aiomysql://fin_user:Fin@2024secure@localhost:3306/financial_analyzer"
```

### 项目中的实际代码（`src/storage/database.py`）

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings  # 从 .env 读取配置

# 创建引擎（会自动读取 .env 中的 MySQL 配置）
engine = create_engine(
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
    echo=False,  # 设为 True 可以看到 SQL 日志
)

# 创建 Session 工厂
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """FastAPI 依赖注入用的数据库 session 生成器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 六、数据库表结构（自动创建）

> 你**不需要手动建表**！项目启动时 SQLAlchemy 会自动创建。但这里是表结构说明，方便你了解。

### `balance_sheets` 表

```sql
CREATE TABLE balance_sheets (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    stock_code    VARCHAR(10) NOT NULL,          -- 股票代码
    report_date   DATE NOT NULL,                  -- 报告期
    total_current_assets    DECIMAL(20,2),        -- 流动资产合计
    total_non_current_assets DECIMAL(20,2),       -- 非流动资产合计
    total_assets            DECIMAL(20,2),        -- 资产总计
    total_current_liabilities DECIMAL(20,2),      -- 流动负债合计
    total_non_current_liabilities DECIMAL(20,2),  -- 非流动负债合计
    total_liabilities       DECIMAL(20,2),        -- 负债合计
    total_equity            DECIMAL(20,2),        -- 所有者权益合计
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (stock_code, report_date)
);
```

### `income_statements` 表

```sql
CREATE TABLE income_statements (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    stock_code    VARCHAR(10) NOT NULL,
    report_date   DATE NOT NULL,
    total_revenue       DECIMAL(20,2),    -- 营业总收入
    operating_cost      DECIMAL(20,2),    -- 营业总成本
    operating_profit    DECIMAL(20,2),    -- 营业利润
    total_profit        DECIMAL(20,2),    -- 利润总额
    net_income          DECIMAL(20,2),    -- 净利润
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (stock_code, report_date)
);
```

### `cashflow_statements` 表

```sql
CREATE TABLE cashflow_statements (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    stock_code    VARCHAR(10) NOT NULL,
    report_date   DATE NOT NULL,
    operating_cashflow  DECIMAL(20,2),    -- 经营现金流净额
    investing_cashflow  DECIMAL(20,2),    -- 投资现金流净额
    financing_cashflow  DECIMAL(20,2),    -- 筹资现金流净额
    net_cashflow        DECIMAL(20,2),    -- 现金净增加额
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (stock_code, report_date)
);
```

### `analysis_reports` 表

```sql
CREATE TABLE analysis_reports (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    stock_code    VARCHAR(10) NOT NULL,
    report_date   DATE NOT NULL,
    analysis_depth VARCHAR(20),           -- basic / detailed / ai_enhanced
    ratios_json   JSON,                   -- 全部比率（JSON格式存储）
    ai_report     TEXT,                   -- AI分析报告文本
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 七、你需要做的操作清单

| 步骤 | 操作 | 命令 | 耗时 |
|------|------|------|------|
| 1 | 确认 MySQL 服务运行中 | `Get-Service -Name "MySQL*"` | 10秒 |
| 2 | 登录 MySQL | `mysql -u root -p` | 30秒 |
| 3 | 创建数据库和用户 | 复制第三节的 SQL 执行 | 1分钟 |
| 4 | 修改密码（可选） | 改 SQL 中的密码 | 30秒 |
| 5 | 配置项目 `.env` | 填入数据库信息 | 1分钟 |
| 6 | 验证连接 | 项目开发后自动测试 | 自动 |

> **总耗时约 3 分钟**，一次性操作，后续不需要再管。

---

## 八、常用 MySQL 命令速查

```sql
-- 查看所有数据库
SHOW DATABASES;

-- 切换到项目数据库
USE financial_analyzer;

-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESCRIBE balance_sheets;

-- 查看某只股票的数据
SELECT * FROM balance_sheets WHERE stock_code = '600519';

-- 查看数据条数
SELECT COUNT(*) FROM balance_sheets;

-- 删除某只股票的数据（谨慎！）
DELETE FROM balance_sheets WHERE stock_code = '600519';

-- 清空整个表（谨慎！）
TRUNCATE TABLE balance_sheets;

-- 退出 MySQL
EXIT;
```

---

## 九、常见问题

### Q1：忘记了 root 密码怎么办？

```powershell
# 1. 停止 MySQL 服务
Stop-Service -Name "MySQL80"

# 2. 以跳过权限方式启动
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --skip-grant-tables

# 3. 另开一个 PowerShell 窗口登录（不需要密码）
mysql -u root

# 4. 重置密码
ALTER USER 'root'@'localhost' IDENTIFIED BY '新密码';
FLUSH PRIVILEGES;
EXIT;

# 5. 停止跳过权限的 mysqld，正常启动服务
# Ctrl+C 停止 mysqld 进程
Start-Service -Name "MySQL80"
```

### Q2：端口 3306 被占用怎么办？

```powershell
# 查看谁在用 3306
netstat -ano | findstr :3306
# 输出中的最后一列是 PID，可以在任务管理器中找到对应进程
```

### Q3：怎么备份数据库？

```powershell
# 导出整个数据库
mysqldump -u fin_user -p financial_analyzer > backup.sql

# 导入备份
mysql -u fin_user -p financial_analyzer < backup.sql
```

### Q4：要不要安装 Redis？

Redis 是缓存层，**不是必须的**。如果暂时不装 Redis，项目会跳过缓存直接请求 AKShare（速度稍慢但功能不受影响）。

如果要装，最简方式：

```powershell
# 用 Docker（推荐）
docker run -d --name redis -p 6379:6379 redis

# 或者下载 Windows 版 Redis
# https://github.com/tporadowski/redis/releases
```
