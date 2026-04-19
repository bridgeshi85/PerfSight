use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::System;

use super::Metric;

fn percent_value(value: f64) -> Value {
    match serde_json::Number::from_f64(value) {
        Some(number) => Value::Number(number),
        None => Value::Number(serde_json::Number::from(0)),
    }
}

pub fn collect_memory_metrics(system: &System) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();

    let total_memory = System::total_memory(system);
    let used_memory = System::used_memory(system);
    let available_memory = System::available_memory(system);
    let free_memory = System::free_memory(system);
    
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
    
    // 扁平化内存指标
    metrics.push(Metric::new(
        "memory_total_bytes".to_string(),
        "memory".to_string(),
        Value::Number(serde_json::Number::from(total_memory)),
        HashMap::new(),
        Some("bytes".to_string()),
    ));
    
    metrics.push(Metric::new(
        "memory_used_bytes".to_string(),
        "memory".to_string(),
        Value::Number(serde_json::Number::from(used_memory)),
        HashMap::new(),
        Some("bytes".to_string()),
    ));
    
    metrics.push(Metric::new(
        "memory_used_percent".to_string(),
        "memory".to_string(),
        percent_value(used_percent),
        HashMap::new(),
        Some("percent".to_string()),
    ));
    
    metrics.push(Metric::new(
        "memory_available_bytes".to_string(),
        "memory".to_string(),
        Value::Number(serde_json::Number::from(available_memory)),
        HashMap::new(),
        Some("bytes".to_string()),
    ));

    metrics.push(Metric::new(
        "memory_free_bytes".to_string(),
        "memory".to_string(),
        Value::Number(serde_json::Number::from(free_memory)),
        HashMap::new(),
        Some("bytes".to_string()),
    ));

    metrics.push(Metric::new(
        "memory_available_percent".to_string(),
        "memory".to_string(),
        percent_value(available_percent),
        HashMap::new(),
        Some("percent".to_string()),
    ));

    // Swap 内存信息
    let total_swap = System::total_swap(system);
    let used_swap = System::used_swap(system);
    let free_swap = System::free_swap(system);
    
    if total_swap > 0 {
        let swap_used_percent = (used_swap as f64 / total_swap as f64) * 100.0;

        metrics.push(Metric::new(
            "swap_total_bytes".to_string(),
            "memory".to_string(),
            Value::Number(serde_json::Number::from(total_swap)),
            HashMap::new(),
            Some("bytes".to_string()),
        ));

        metrics.push(Metric::new(
            "swap_used_bytes".to_string(),
            "memory".to_string(),
            Value::Number(serde_json::Number::from(used_swap)),
            HashMap::new(),
            Some("bytes".to_string()),
        ));

        metrics.push(Metric::new(
            "swap_free_bytes".to_string(),
            "memory".to_string(),
            Value::Number(serde_json::Number::from(free_swap)),
            HashMap::new(),
            Some("bytes".to_string()),
        ));

        metrics.push(Metric::new(
            "swap_used_percent".to_string(),
            "memory".to_string(),
            percent_value(swap_used_percent),
            HashMap::new(),
            Some("percent".to_string()),
        ));
    }
    
    Ok(metrics)
}