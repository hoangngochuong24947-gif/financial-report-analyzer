# 📊 财务报表分析系统 / Financial Report Analyzer

A股上市公司财务报表自动分析系统，支持三大报表获取、财务比率计算、杜邦分析、趋势分析和AI智能报告生成。

## 功能特性

- 📈 自动获取A股上市公司三大财务报表（资产负债表、利润表、现金流量表）
- 🧮 财务比率计算（盈利能力、偿债能力、运营效率）
- 🔍 杜邦分析、现金流分析、趋势分析
- 🤖 基于LLM的智能财务分析报告
- 📊 数据可视化与Excel导出
- 💾 MySQL持久化 + Redis缓存

## 技术栈

- **后端**: FastAPI + Python 3.10+
- **数据源**: AKShare（免费，无需API Key）
- **数据处理**: pandas + NumPy
- **数据验证**: pydantic（Decimal精度保证）
- **数据库**: MySQL + Redis
- **LLM**: DeepSeek API
- **日志**: Loguru

## 快速开始

### 1. 安装依赖

```bash
# 使用 Poetry
poetry install

# 或使用 pip
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入数据库和API配置
```

### 3. 启动服务

```bash
poetry run uvicorn src.main:app --reload
```

访问 <http://localhost:8000/docs> 查看API文档

## 项目结构

详见 [docs/](docs/) 目录下的完整文档。

## License

MIT
