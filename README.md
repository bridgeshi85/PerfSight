# PerfSight - 云原生压测智能分析平台

> **核心理念**: One-Command Deploy, Zero-Touch Observe, AI-Driven Analysis  
> **中文理念**: 一键部署，零触监控，AI 驱动分析

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/rust-%23000000.svg?style=flat&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/python-3670A0?style=flat&logo=python&logoColor=ffdd54)](https://www.python.org/)

## 📋 项目概述

PerfSight 是一个集成了压测执行、实时监控、智能分析和报告生成的云原生性能分析平台。通过现代化的技术栈和AI驱动的分析能力，为开发者和运维团队提供从压测到诊断的全链路解决方案。

### 解决的核心痛点
- 传统压测工具配置复杂，缺乏实时监控
- 性能分析依赖人工经验，难以快速定位根因
- 监控数据与分析报告分离，缺乏一站式解决方案
- 数据库性能监控与业务压测数据难以关联分析

## 🚀 核心功能

- **🔧 一键部署**：通过单一命令启动完整压测分析流水线，支持 Docker 容器化部署
- **📊 零触监控**：Rust Agent 自动采集系统性能指标（CPU、内存、磁盘、网络等）
- **⚡ 压测集成**：支持主流的 K6 压测工具，可执行压力、冒烟、耐久等多种测试场景
- **🧠 AI 驱动分析**：调用 LLM（如 OpenAI）进行异常检测、根因定位与优化建议生成
- **📈 智能报告**：自动化生成包含可视化图表与 AI 诊断建议的 HTML/PDF 报告

## 🏗️ 技术架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Rust Agent    │────▶│  数据文件存储   │────▶│  Python分析引擎 │
│   (性能采集)    │     │  (JSON/CSV)     │     │  (Pandas/图表)  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  PG监控(可选)   │────▶│   LLM智能分析   │────▶│  报告生成器     │
│                 │     │                 │     │  (HTML/PDF)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 📦 技术栈

- **后端/代理**：Rust（高性能、内存安全）
- **数据分析**：Python, Pandas, NumPy
- **可视化**：Matplotlib, Plotly, Seaborn
- **AI分析**：OpenAI API/Claude API/本地LLM
- **报告生成**：Jinja2（HTML）、WeasyPrint（PDF）
- **数据库监控**：psycopg2（PostgreSQL）

## 🚀 快速开始

### 环境要求

- **Rust**: 1.70+
- **Python**: 3.8+
- **操作系统**: Linux, macOS, Windows

### 1. 克隆项目

```bash
git clone https://github.com/your-org/perfsight.git
cd perfsight
```

### 2. 部署 Rust Agent

```bash
cd rust-agent
# 一键部署并启动监控
./scripts/deploy.sh

# 或者手动构建
cargo build --release
./target/release/perfsight-agent start
```

#### Rust Agent 使用示例

```bash
# 生成默认配置文件
./target/release/perfsight-agent init-config

# 启动监控（5秒间隔，JSON格式）
./target/release/perfsight-agent start -i 5 -f json -o ./output

# 显示系统信息
./target/release/perfsight-agent info

# 运行300秒后停止
./target/release/perfsight-agent start -d 300
```

### 3. 安装 Python Analytics

```bash
cd python-analytics
pip install -r requirements.txt
```

### 4. 配置 AI 分析（可选）

创建 `.env` 文件：

```bash
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key

# 或 Anthropic 配置
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 5. 运行分析

```bash
cd python-analytics

# 生成默认配置
python main.py init-config

# 分析数据并生成报告
python main.py analyze -i ../rust-agent/output -o ./reports --ai-analysis

# 仅生成图表
python main.py visualize -i ../rust-agent/output/data.json -o ./charts

# 查看数据信息
python main.py info -i ../rust-agent/output
```

## 📊 使用流程

1. **部署**：一键部署 Rust Agent 到目标服务器
2. **采集**：Agent 自动采集性能指标并保存
3. **分析**：Python 引擎处理数据，调用 LLM 进行智能分析
4. **报告**：自动生成包含图表和 AI 建议的报告
5. **预警**：（可选）设置阈值告警

## 📁 项目结构

```
PerfSight/
├── README.md                    # 项目说明文档
├── LICENSE                      # 开源协议
├── .gitignore                   # Git 忽略文件
├── rust-agent/                  # Rust 监控代理
│   ├── Cargo.toml              # Rust 项目配置
│   ├── src/                    # 源代码
│   │   ├── main.rs             # CLI 入口
│   │   ├── collector/          # 指标采集模块
│   │   ├── exporter/           # 数据导出模块
│   │   └── config/             # 配置管理
│   └── scripts/
│       └── deploy.sh           # 一键部署脚本
├── python-analytics/            # Python 分析引擎
│   ├── requirements.txt        # Python 依赖
│   ├── main.py                 # 分析引擎入口
│   ├── data_processor/         # 数据处理模块
│   │   ├── cleaner.py          # 数据清洗
│   │   ├── analyzer.py         # 数据分析
│   │   └── visualizer.py       # 图表生成
│   ├── ai_diagnosis/           # AI 诊断模块
│   │   ├── llm_client.py       # LLM 客户端
│   │   └── analyzer.py         # AI 分析逻辑
│   ├── report_generator/       # 报告生成器
│   │   └── report_builder.py   # 报告构建器
│   └── config/
│       └── settings.py         # 配置文件
├── database-monitor/            # 数据库监控模块（可选）
├── examples/                    # 使用示例
├── docs/                        # 文档目录
└── tests/                       # 测试目录
```

## 🔧 配置说明

### Rust Agent 配置

创建 `config.toml`：

```toml
[monitoring]
enable_cpu = true
enable_memory = true
enable_disk = true
enable_network = true
enable_processes = false
cpu_interval_ms = 1000
disk_mount_points = ["/"]
network_interfaces = []

[export]
retention_days = 7
compress_old_data = true
file_prefix = "perfsight"
include_timestamp = true
```

### Python Analytics 配置

创建 `config.yaml`：

```yaml
ai_analysis:
  provider: "openai"  # openai, anthropic, local
  openai_model: "gpt-4"
  enable_anomaly_detection: true
  enable_root_cause_analysis: true
  enable_optimization_suggestions: true

visualization:
  style: "seaborn-v0_8"
  color_palette: "husl"
  figure_size: [12, 8]
  enable_interactive: true

report:
  include_charts: true
  include_ai_analysis: true
  include_recommendations: true
  html_theme: "bootstrap"
```

## 📈 示例报告

生成的报告包含以下内容：

- **📊 数据概览**：总记录数、监控时长、指标类型统计
- **⚡ 性能指标分析**：CPU、内存、磁盘、网络使用情况
- **📈 数据可视化**：时间序列图、分布图、相关性热力图
- **🧠 AI 智能分析**：异常检测、根因分析、性能评估
- **💡 优化建议**：基于 AI 分析的具体改进建议

## 🤖 AI 功能

### 支持的 LLM 提供商

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3-sonnet, Claude-3-haiku
- **本地模型**: 支持兼容 OpenAI API 的本地部署模型

### AI 分析能力

- **异常检测**：自动识别性能指标中的异常模式
- **根因分析**：基于多维度数据分析问题根本原因
- **优化建议**：提供具体的性能优化建议
- **风险评估**：评估系统性能风险等级

## 🔍 监控指标

### 系统指标
- **CPU**: 使用率、频率、负载平均值
- **内存**: 使用率、可用内存、Swap 使用情况
- **磁盘**: 使用率、可用空间、I/O 统计
- **网络**: 接收/发送字节数、数据包统计、错误率

### 进程指标（可选）
- **进程列表**: CPU/内存占用最高的进程
- **进程状态**: 运行状态、父进程关系

## 🚀 部署选项

### 本地部署

```bash
# 克隆项目
git clone https://github.com/your-org/perfsight.git
cd perfsight

# 部署 Rust Agent
cd rust-agent && ./scripts/deploy.sh

# 安装 Python 依赖
cd ../python-analytics && pip install -r requirements.txt
```

### Docker 部署（计划中）

```bash
# 构建镜像
docker build -t perfsight .

# 运行容器
docker run -d --name perfsight -v /data:/app/data perfsight
```

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/your-org/perfsight.git
cd perfsight

# 安装 Rust 依赖
cd rust-agent && cargo build

# 安装 Python 依赖
cd ../python-analytics && pip install -r requirements.txt

# 运行测试
cargo test
python -m pytest
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [sysinfo](https://github.com/GuillaumeGomez/sysinfo) - Rust 系统信息库
- [pandas](https://pandas.pydata.org/) - Python 数据分析库
- [matplotlib](https://matplotlib.org/) - Python 绘图库
- [OpenAI](https://openai.com/) - AI 分析能力支持

## 📞 联系我们

- **项目主页**: https://github.com/your-org/perfsight
- **问题反馈**: https://github.com/your-org/perfsight/issues
- **讨论区**: https://github.com/your-org/perfsight/discussions

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！