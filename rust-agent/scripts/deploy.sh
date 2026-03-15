#!/bin/bash

# PerfSight Agent 一键部署脚本
# 用法: ./deploy.sh [选项]

set -e

# 默认配置
DEFAULT_OUTPUT_DIR="./output"
DEFAULT_CONFIG_FILE="./config.toml"
DEFAULT_INTERVAL=5
DEFAULT_FORMAT="json"
DEFAULT_DURATION=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
PerfSight Agent 一键部署脚本

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -o, --output DIR        输出目录 (默认: $DEFAULT_OUTPUT_DIR)
    -c, --config FILE       配置文件路径 (默认: $DEFAULT_CONFIG_FILE)
    -i, --interval SECONDS  采集间隔秒数 (默认: $DEFAULT_INTERVAL)
    -f, --format FORMAT     输出格式 json|csv (默认: $DEFAULT_FORMAT)
    -d, --duration SECONDS  运行时长，0表示无限运行 (默认: $DEFAULT_DURATION)
    --build-only            仅构建，不运行
    --init-config           生成默认配置文件并退出
    --clean                 清理构建产物

示例:
    $0                                    # 使用默认配置运行
    $0 -i 10 -f csv                      # 10秒间隔，CSV格式输出
    $0 -d 300                            # 运行5分钟后停止
    $0 --init-config                     # 生成默认配置文件
    $0 --build-only                      # 仅构建二进制文件
    $0 --clean                           # 清理构建产物

EOF
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    if ! command -v cargo &> /dev/null; then
        print_error "未找到 Rust/Cargo，请先安装 Rust: https://rustup.rs/"
        exit 1
    fi
    
    print_success "依赖检查通过"
}

# 构建项目
build_project() {
    print_info "构建 PerfSight Agent..."
    
    cd "$(dirname "$0")/.."
    
    if [ "$1" = "release" ]; then
        cargo build --release
        BINARY_PATH="target/release/perfsight-agent"
    else
        cargo build
        BINARY_PATH="target/debug/perfsight-agent"
    fi
    
    if [ ! -f "$BINARY_PATH" ]; then
        print_error "构建失败，未找到二进制文件"
        exit 1
    fi
    
    print_success "构建完成: $BINARY_PATH"
}

# 生成配置文件
init_config() {
    print_info "生成默认配置文件..."
    
    if [ -f "$CONFIG_FILE" ]; then
        print_warning "配置文件已存在: $CONFIG_FILE"
        read -p "是否覆盖? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "跳过配置文件生成"
            return
        fi
    fi
    
    $BINARY_PATH init-config --output "$CONFIG_FILE"
    print_success "配置文件已生成: $CONFIG_FILE"
}

# 运行监控
run_monitoring() {
    print_info "启动 PerfSight Agent 监控..."
    print_info "配置: 输出目录=$OUTPUT_DIR, 间隔=${INTERVAL}s, 格式=$FORMAT"
    
    if [ "$DURATION" -gt 0 ]; then
        print_info "运行时长: ${DURATION}s"
    else
        print_info "运行时长: 无限制 (按 Ctrl+C 停止)"
    fi
    
    # 创建输出目录
    mkdir -p "$OUTPUT_DIR"
    
    # 运行监控
    $BINARY_PATH start \
        --config "$CONFIG_FILE" \
        --output "$OUTPUT_DIR" \
        --interval "$INTERVAL" \
        --format "$FORMAT" \
        --duration "$DURATION"
}

# 清理构建产物
clean_build() {
    print_info "清理构建产物..."
    cd "$(dirname "$0")/.."
    cargo clean
    print_success "清理完成"
}

# 解析命令行参数
OUTPUT_DIR="$DEFAULT_OUTPUT_DIR"
CONFIG_FILE="$DEFAULT_CONFIG_FILE"
INTERVAL="$DEFAULT_INTERVAL"
FORMAT="$DEFAULT_FORMAT"
DURATION="$DEFAULT_DURATION"
BUILD_ONLY=false
INIT_CONFIG_ONLY=false
CLEAN_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -i|--interval)
            INTERVAL="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --init-config)
            INIT_CONFIG_ONLY=true
            shift
            ;;
        --clean)
            CLEAN_ONLY=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 主逻辑
main() {
    print_info "PerfSight Agent 部署脚本启动"
    
    if [ "$CLEAN_ONLY" = true ]; then
        clean_build
        exit 0
    fi
    
    check_dependencies
    build_project
    
    if [ "$INIT_CONFIG_ONLY" = true ]; then
        init_config
        exit 0
    fi
    
    if [ "$BUILD_ONLY" = true ]; then
        print_success "构建完成，跳过运行"
        exit 0
    fi
    
    # 如果配置文件不存在，生成默认配置
    if [ ! -f "$CONFIG_FILE" ]; then
        init_config
    fi
    
    run_monitoring
}

# 信号处理
trap 'print_info "收到停止信号，正在退出..."; exit 0' INT TERM

# 运行主函数
main "$@"