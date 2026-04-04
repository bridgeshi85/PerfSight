use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::{Pid, System};
use super::Metric;

pub fn collect_process_metrics(system: &System) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();
    
    // 进程总数
    let process_count = system.processes().len();
    metrics.push(Metric::new(
        "process_count".to_string(),
        "process_count".to_string(),
        Value::Number(serde_json::Number::from(process_count)),
        HashMap::new(),
        Some("count".to_string()),
    ));
    
    // 收集 CPU 和内存使用率最高的前 10 个进程
    let mut processes: Vec<_> = system.processes().iter().collect();
    processes.sort_by(|a, b| {
        b.1.cpu_usage().partial_cmp(&a.1.cpu_usage()).unwrap_or(std::cmp::Ordering::Equal)
    });
    
    for (i, (pid, process)) in processes.iter().take(10).enumerate() {
        let mut labels = HashMap::new();
        labels.insert("pid".to_string(), pid.to_string());
        labels.insert("name".to_string(), process.name().to_string_lossy().to_string());
        labels.insert("rank".to_string(), (i + 1).to_string());
        
        let mut process_details = serde_json::Map::new();
        process_details.insert("pid".to_string(), Value::Number(serde_json::Number::from(pid.as_u32())));
        process_details.insert("name".to_string(), Value::String(process.name().to_string_lossy().to_string()));
        process_details.insert("cpu_usage".to_string(), Value::Number(serde_json::Number::from_f64(process.cpu_usage() as f64).unwrap()));
        process_details.insert("memory_bytes".to_string(), Value::Number(serde_json::Number::from(process.memory())));
        process_details.insert("virtual_memory_bytes".to_string(), Value::Number(serde_json::Number::from(process.virtual_memory())));
        process_details.insert("status".to_string(), Value::String(format!("{:?}", process.status())));
        
        if let Some(parent) = process.parent() {
            process_details.insert("parent_pid".to_string(), Value::Number(serde_json::Number::from(parent.as_u32())));
        }
        
        metrics.push(Metric::new(
            "top_process".to_string(),
            "top_process".to_string(),
            Value::Object(process_details),
            labels,
            None,
        ));
    }
    
    // 按内存使用排序的前 10 个进程
    processes.sort_by(|a, b| {
        b.1.memory().cmp(&a.1.memory())
    });
    
    for (i, (pid, process)) in processes.iter().take(10).enumerate() {
        let mut labels = HashMap::new();
        labels.insert("pid".to_string(), pid.to_string());
        labels.insert("name".to_string(), process.name().to_string_lossy().to_string());
        labels.insert("rank".to_string(), (i + 1).to_string());
        
        metrics.push(Metric::new(
            "top_memory_process".to_string(),
            "top_memory_process".to_string(),
            Value::Number(serde_json::Number::from(process.memory())),
            labels,
            Some("bytes".to_string()),
        ));
    }
    
    Ok(metrics)
}