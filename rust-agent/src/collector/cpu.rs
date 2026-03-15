use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::{System, SystemExt, CpuExt};

use super::Metric;

pub fn collect_cpu_metrics(system: &System) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();
    
    // 整体 CPU 使用率
    let global_cpu_usage = system.global_cpu_info().cpu_usage();
    metrics.push(Metric::new(
        "cpu_usage_percent".to_string(),
        "cpu_usage".to_string(),
        Value::Number(serde_json::Number::from_f64(global_cpu_usage as f64).unwrap()),
        HashMap::new(),
        Some("percent".to_string()),
    ));
    
    // 各个 CPU 核心的使用率
    for (i, cpu) in system.cpus().iter().enumerate() {
        let mut labels = HashMap::new();
        labels.insert("cpu_core".to_string(), i.to_string());
        labels.insert("cpu_name".to_string(), cpu.name().to_string());
        
        metrics.push(Metric::new(
            "cpu_core_usage_percent".to_string(),
            "cpu_core_usage".to_string(),
            Value::Number(serde_json::Number::from_f64(cpu.cpu_usage() as f64).unwrap()),
            labels,
            Some("percent".to_string()),
        ));
    }
    
    // CPU 频率信息
    for (i, cpu) in system.cpus().iter().enumerate() {
        let mut labels = HashMap::new();
        labels.insert("cpu_core".to_string(), i.to_string());
        
        metrics.push(Metric::new(
            "cpu_frequency_mhz".to_string(),
            "cpu_frequency".to_string(),
            Value::Number(serde_json::Number::from(cpu.frequency())),
            labels,
            Some("MHz".to_string()),
        ));
    }
    
    // 负载平均值（仅在支持的系统上）
    if let Some(load_avg) = system.load_average().one {
        metrics.push(Metric::new(
            "load_average_1min".to_string(),
            "load_average".to_string(),
            Value::Number(serde_json::Number::from_f64(load_avg).unwrap()),
            HashMap::new(),
            None,
        ));
    }
    
    if let Some(load_avg) = system.load_average().five {
        metrics.push(Metric::new(
            "load_average_5min".to_string(),
            "load_average".to_string(),
            Value::Number(serde_json::Number::from_f64(load_avg).unwrap()),
            HashMap::new(),
            None,
        ));
    }
    
    if let Some(load_avg) = system.load_average().fifteen {
        metrics.push(Metric::new(
            "load_average_15min".to_string(),
            "load_average".to_string(),
            Value::Number(serde_json::Number::from_f64(load_avg).unwrap()),
            HashMap::new(),
            None,
        ));
    }
    
    Ok(metrics)
}