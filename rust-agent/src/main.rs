use anyhow::Result;
use clap::{Parser, Subcommand};
use log::{info, warn};
use std::path::PathBuf;
use std::time::Duration;

mod collector;
mod config;
mod exporter;

use collector::MetricsCollector;
use config::AgentConfig;
use exporter::{Exporter, ExportFormat};

#[derive(Parser)]
#[command(name = "perfsight-agent")]
#[command(about = "PerfSight 高性能系统监控代理")]
#[command(version = "0.1.0")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// 启动监控代理
    Start {
        /// 配置文件路径
        #[arg(short, long, default_value = "config.toml")]
        config: PathBuf,
        /// 输出目录
        #[arg(short, long, default_value = "output")]
        output: PathBuf,
        /// 采集间隔（秒）
        #[arg(short, long, default_value = "5")]
        interval: u64,
        /// 输出格式
        #[arg(short, long, default_value = "json")]
        format: ExportFormat,
        /// 运行时长（秒），0表示无限运行
        #[arg(short, long, default_value = "0")]
        duration: u64,
    },
    /// 生成默认配置文件
    InitConfig {
        /// 配置文件输出路径
        #[arg(short, long, default_value = "config.toml")]
        output: PathBuf,
    },
    /// 显示系统信息
    Info,
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();
    
    let cli = Cli::parse();
    
    match cli.command {
        Commands::Start {
            config,
            output,
            interval,
            format,
            duration,
        } => {
            info!("启动 PerfSight Agent...");
            start_monitoring(config, output, interval, format, duration).await?;
        }
        Commands::InitConfig { output } => {
            info!("生成默认配置文件: {:?}", output);
            AgentConfig::generate_default_config(&output)?;
            println!("✅ 默认配置文件已生成: {:?}", output);
        }
        Commands::Info => {
            info!("显示系统信息");
            show_system_info().await?;
        }
    }
    
    Ok(())
}

async fn start_monitoring(
    config_path: PathBuf,
    output_dir: PathBuf,
    interval: u64,
    format: ExportFormat,
    duration: u64,
) -> Result<()> {
    // 加载配置
    let config = if config_path.exists() {
        AgentConfig::load_from_file(&config_path)?
    } else {
        warn!("配置文件不存在，使用默认配置");
        AgentConfig::default()
    };
    
    // 创建输出目录
    std::fs::create_dir_all(&output_dir)?;
    
    // 初始化采集器和导出器
    let collector = MetricsCollector::new(config.clone());
    let exporter = Exporter::new(output_dir, format);
    
    info!("开始监控，采集间隔: {}秒", interval);
    
    let interval_duration = Duration::from_secs(interval);
    let start_time = std::time::Instant::now();
    let max_duration = if duration > 0 {
        Some(Duration::from_secs(duration))
    } else {
        None
    };
    
    loop {
        // 检查是否超过运行时长
        if let Some(max_dur) = max_duration {
            if start_time.elapsed() >= max_dur {
                info!("达到最大运行时长，停止监控");
                break;
            }
        }
        
        // 采集指标
        match collector.collect_all().await {
            Ok(metrics) => {
                info!("采集到 {} 个指标", metrics.len());
                
                // 导出数据
                if let Err(e) = exporter.export(&metrics).await {
                    warn!("导出数据失败: {}", e);
                }
            }
            Err(e) => {
                warn!("采集指标失败: {}", e);
            }
        }
        
        // 等待下次采集
        tokio::time::sleep(interval_duration).await;
    }
    
    info!("监控已停止");
    Ok(())
}

async fn show_system_info() -> Result<()> {
    let collector = MetricsCollector::new(AgentConfig::default());
    let metrics = collector.collect_all().await?;
    
    println!("🖥️  系统信息概览");
    println!("================");
    
    for metric in metrics {
        match metric.metric_type.as_str() {
            "system_info" => {
                if let Some(value) = metric.value.as_object() {
                    if let Some(hostname) = value.get("hostname") {
                        println!("主机名: {}", hostname.as_str().unwrap_or("未知"));
                    }
                    if let Some(os) = value.get("os_name") {
                        println!("操作系统: {}", os.as_str().unwrap_or("未知"));
                    }
                    if let Some(arch) = value.get("architecture") {
                        println!("架构: {}", arch.as_str().unwrap_or("未知"));
                    }
                }
            }
            "cpu_usage" => {
                if let Some(usage) = metric.value.as_f64() {
                    println!("CPU 使用率: {:.2}%", usage);
                }
            }
            "memory_usage" => {
                if let Some(value) = metric.value.as_object() {
                    if let Some(used_percent) = value.get("used_percent") {
                        println!("内存使用率: {:.2}%", used_percent.as_f64().unwrap_or(0.0));
                    }
                }
            }
            _ => {}
        }
    }
    
    Ok(())
}