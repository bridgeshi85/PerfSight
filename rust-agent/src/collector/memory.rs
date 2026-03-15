use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::{System, SystemExt};

use super::Metric;

pub fn collect_memory_metrics(system: &System) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();
    
    let total_memory = system.total_memory();
    let used_memory = system.used_memory();
    let available_memory = system.available_memory();
    let free_memory = system.free_memory();
    
    // 内存使用率
    let used_percent = if total_memory > 0 {
        (used_memory as f64 / total_memory as f64) * 100.0
    } else {
        0.0
    };
    
    let available_percent = if total_memory > 0 {
        (available_memory as f64 / total_memory as f64) * 100.0
    } else {
        0.0
    };
    
    // 内存使用详情
    let mut memory_details = serde_json::Map::new();
    memory_details.insert("total_bytes".to_string(), Value::Number(serde_json::Number::from(total_memory)));
    memory_details.insert("used_bytes".to_string(), Value::Number(serde_json::Number::from(used_memory)));
    memory_details.insert("available_bytes".to_string(), Value::Number(serde_json::Number::from(available_memory)));
    memory_details.insert("free_bytes".to_string(), Value::Number(serde_json::Number::from(free_memory)));
    memory_details.insert("used_percent".to_string(), Value::Number(serde_json::Number::from_f64(used_percent).unwrap()));
    memory_details.insert("available_percent".to_string(), Value::Number(serde_json::Number::from_f64(available_percent).unwrap()));
    
    metrics.push(Metric::new(
        "memory_usage".to_string(),
        "memory_usage".to_string(),
        Value::Object(memory_details),
        HashMap::new(),
        None,
    ));
    
    // 单独的内存指标
    metrics.push(Metric::new(
        "memory_total_bytes".to_string(),
        "memory_total".to_string(),
        Value::Number(serde_json::Number::from(total_memory)),
        HashMap::new(),
        Some("bytes".to_string()),
    ));
    
    metrics.push(Metric::new(
        "memory_used_bytes".to_string(),
        "memory_used".to_string(),
        Value::Number(serde_json::Number::from(used_memory)),
        HashMap::new(),
        Some("bytes".to_string()),
    ));
    
    metrics.push(Metric::new(
        "memory_used_percent".to_string(),
        "memory_used_percent".to_string(),
        Value::Number(serde_json::Number::from_f64(used_percent).unwrap()),
        HashMap::new(),
        Some("percent".to_string()),
    ));
    
    metrics.push(Metric::new(
        "memory_available_bytes".to_string(),
        "memory_available".to_string(),
        Value::Number(serde_json::Number::from(available_memory)),
        HashMap::new(),
        Some("bytes".to_string()),
    ));
    
    // Swap 内存信息
    let total_swap = system.total_swap();
    let used_swap = system.used_swap();
    let free_swap = system.free_swap();
    
    if total_swap > 0 {
        let swap_used_percent = (used_swap as f64 / total_swap as f64) * 100.0;
        
        let mut swap_details = serde_json::Map::new();
        swap_details.insert("total_bytes".to_string(), Value::Number(serde_json::Number::from(total_swap)));
        swap_details.insert("used_bytes".to_string(), Value::Number(serde_json::Number::from(used_swap)));
        swap_details.insert("free_bytes".to_string(), Value::Number(serde_json::Number::from(free_swap)));
        swap_details.insert("used_percent".to_string(), Value::Number(serde_json::Number::from_f64(swap_used_percent).unwrap()));
        
        metrics.push(Metric::new(
            "swap_usage".to_string(),
            "swap_usage".to_string(),
            Value::Object(swap_details),
            HashMap::new(),
            None,
        ));
    }
    
    Ok(metrics)
}