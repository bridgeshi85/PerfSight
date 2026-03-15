#!/bin/bash

# PerfSight 快速开始演示脚本

set -e

echo "🚀 PerfSight 快速开始演示"
echo "=========================="

# 检查依赖
echo "📋 检查依赖..."
if ! command -v cargo &> /dev/null; then
    echo "❌ 未找到 Rust/Cargo，请先安装: https://rustup.rs/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

echo "✅ 依赖检查通过"

# 构建 Rust Agent
echo ""
echo "🔨 构建 Rust Agent..."
cd rust-agent
cargo build --release
echo "✅ Rust Agent 构建完成"

# 生成配置文件
echo ""
echo "⚙️ 生成配置文件..."
./target/release/perfsight-agent init-config --output config.toml
echo "✅ 配置文件已生成"

# 启动短期监控（30秒）
echo ""
echo "📊 启动性能监控（30秒）..."
mkdir -p output
./target/release/perfsight-agent start \
    --config config.toml \
    --output output \
    --interval 2 \
    --format json \
    --duration 30 &

AGENT_PID=$!
echo "✅ 监控已启动，PID: $AGENT_PID"

# 等待监控完成
echo "⏳ 等待监控完成..."
wait $AGENT_PID
echo "✅ 监控完成"

# 安装 Python 依赖
echo ""
echo "📦 安装 Python 依赖..."
cd ../python-analytics
pip install -r requirements.txt
echo "✅ Python 依赖安装完成"

# 生成分析报告
echo ""
echo "📈 生成分析报告..."
python main.py analyze \
    --input-dir ../rust-agent/output \
    --output-dir ./reports \
    --format html

echo ""
echo "🎉 演示完成！"
echo "📄 查看报告: python-analytics/reports/"
echo "📊 查看数据: rust-agent/output/"