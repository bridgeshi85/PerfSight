use anyhow::Result;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::System;

use crate::config::AgentConfig;

pub mod cpu;
pub mod memory;
pub mod disk;
pub mod network;
pub mod process;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metric {
    /// 指标名称
    pub name: String,
    /// 指标类型
    pub metric_type: String,
    /// 指标值
    pub value: Value,
    /// 时间戳
    pub timestamp: DateTime<Utc>,
    /// 标签
    pub labels: HashMap<String, String>,
    /// 单位
    pub unit: Option<String>,
}

impl Metric {
    pub fn new(
        name: String,
        metric_type: String,
        value: Value,
        labels: HashMap<String, String>,
        unit: Option<String>,
    ) -> Self {
        Self {
            name,
            metric_type,
            value,
            timestamp: Utc::now(),
            labels,
            unit,
        }
    }
}

pub struct MetricsCollector {
    config: AgentConfig,
    system: System,
}

impl MetricsCollector {
    pub fn new(config: AgentConfig) -> Self {
        let mut system = System::new_all();
        system.refresh_all();
        
        Self { config, system }
    }
    
    /// 采集所有启用的指标
    pub async fn collect_all(&mut self) -> Result<Vec<Metric>> {
        let mut metrics = Vec::new();
        
        // 刷新系统信息
        self.system.refresh_all();
        
        // 采集系统基本信息
        metrics.extend(self.collect_system_info()?);
        
        // 根据配置采集各类指标
        if self.config.monitoring.enable_cpu {
            metrics.extend(self.collect_cpu_metrics()?);
        }
        
        if self.config.monitoring.enable_memory {
            metrics.extend(self.collect_memory_metrics()?);
        }
        
        if self.config.monitoring.enable_disk {
            metrics.extend(self.collect_disk_metrics()?);
        }
        
        if self.config.monitoring.enable_network {
            metrics.extend(self.collect_network_metrics()?);
        }
        
        if self.config.monitoring.enable_processes {
            metrics.extend(self.collect_process_metrics()?);
        }
        
        Ok(metrics)
    }
    
    /// 采集系统基本信息
    fn collect_system_info(&self) -> Result<Vec<Metric>> {
        let mut metrics = Vec::new();
        let mut labels = HashMap::new();
        
        // 主机名
        if let Some(hostname) = System::host_name() {
            labels.insert("hostname".to_string(), hostname);
        }
        
        let mut system_info = serde_json::Map::new();
        system_info.insert("hostname".to_string(),
            Value::String(System::host_name().unwrap_or_else(|| "unknown".to_string())));
        system_info.insert("os_name".to_string(),
            Value::String(System::name().unwrap_or_else(|| "unknown".to_string())));
        system_info.insert("os_version".to_string(),
            Value::String(System::os_version().unwrap_or_else(|| "unknown".to_string())));
        system_info.insert("kernel_version".to_string(),
            Value::String(System::kernel_version().unwrap_or_else(|| "unknown".to_string())));
        system_info.insert("architecture".to_string(),
            Value::String(std::env::consts::ARCH.to_string()));
        system_info.insert("cpu_count".to_string(),
            Value::Number(serde_json::Number::from(self.system.cpus().len())));
        system_info.insert("total_memory".to_string(),
            Value::Number(serde_json::Number::from(self.system.total_memory())));
        
        metrics.push(Metric::new(
            "system_info".to_string(),
            "system_info".to_string(),
            Value::Object(system_info),
            labels,
            None,
        ));
        
        Ok(metrics)
    }
    
    /// 采集 CPU 指标
    fn collect_cpu_metrics(&self) -> Result<Vec<Metric>> {
        cpu::collect_cpu_metrics(&self.system)
    }
    
    /// 采集内存指标
    fn collect_memory_metrics(&self) -> Result<Vec<Metric>> {
        memory::collect_memory_metrics(&self.system)
    }
    
    /// 采集磁盘指标
    fn collect_disk_metrics(&self) -> Result<Vec<Metric>> {
        disk::collect_disk_metrics(&self.system, &self.config.monitoring.disk_mount_points)
    }
    
    /// 采集网络指标
    fn collect_network_metrics(&self) -> Result<Vec<Metric>> {
        network::collect_network_metrics(&self.system, &self.config.monitoring.network_interfaces)
    }
    
    /// 采集进程指标
    fn collect_process_metrics(&self) -> Result<Vec<Metric>> {
        process::collect_process_metrics(&self.system)
    }
}