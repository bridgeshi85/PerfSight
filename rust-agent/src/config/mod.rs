use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentConfig {
    /// 监控配置
    pub monitoring: MonitoringConfig,
    /// 导出配置
    pub export: ExportConfig,
    /// 数据库监控配置（可选）
    pub database: Option<DatabaseConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitoringConfig {
    /// 是否启用 CPU 监控
    pub enable_cpu: bool,
    /// 是否启用内存监控
    pub enable_memory: bool,
    /// 是否启用磁盘监控
    pub enable_disk: bool,
    /// 是否启用网络监控
    pub enable_network: bool,
    /// 是否启用进程监控
    pub enable_processes: bool,
    /// CPU 采集间隔（毫秒）
    pub cpu_interval_ms: u64,
    /// 监控的磁盘挂载点
    pub disk_mount_points: Vec<String>,
    /// 监控的网络接口
    pub network_interfaces: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportConfig {
    /// 数据保留天数
    pub retention_days: u32,
    /// 是否压缩旧数据
    pub compress_old_data: bool,
    /// 文件名前缀
    pub file_prefix: String,
    /// 是否包含时间戳
    pub include_timestamp: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    /// PostgreSQL 连接配置
    pub postgresql: Option<PostgreSQLConfig>,
    /// Redis 连接配置
    pub redis: Option<RedisConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PostgreSQLConfig {
    /// 连接字符串
    pub connection_string: String,
    /// 是否启用监控
    pub enabled: bool,
    /// 监控查询列表
    pub monitor_queries: Vec<String>,
    /// 查询超时时间（秒）
    pub query_timeout_secs: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RedisConfig {
    /// Redis 连接地址
    pub host: String,
    /// Redis 端口
    pub port: u16,
    /// 密码（可选）
    pub password: Option<String>,
    /// 数据库编号
    pub database: u8,
    /// 是否启用监控
    pub enabled: bool,
}

impl Default for AgentConfig {
    fn default() -> Self {
        Self {
            monitoring: MonitoringConfig {
                enable_cpu: true,
                enable_memory: true,
                enable_disk: true,
                enable_network: true,
                enable_processes: false,
                cpu_interval_ms: 1000,
                disk_mount_points: vec!["/".to_string()],
                network_interfaces: vec![], // 空表示监控所有接口
            },
            export: ExportConfig {
                retention_days: 7,
                compress_old_data: true,
                file_prefix: "perfsight".to_string(),
                include_timestamp: true,
            },
            database: None,
        }
    }
}

impl AgentConfig {
    /// 从文件加载配置
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: AgentConfig = toml::from_str(&content)?;
        Ok(config)
    }
    
    /// 保存配置到文件
    pub fn save_to_file<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        let content = toml::to_string_pretty(self)?;
        std::fs::write(path, content)?;
        Ok(())
    }
    
    /// 生成默认配置文件
    pub fn generate_default_config<P: AsRef<Path>>(path: P) -> Result<()> {
        let default_config = Self::default();
        default_config.save_to_file(path)?;
        Ok(())
    }
}