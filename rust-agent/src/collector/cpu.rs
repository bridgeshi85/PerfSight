use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::System;

use super::Metric;

pub fn collect_cpu_metrics(system: &System) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();
    
    // 整体 CPU 使用率
    let global_cpu_usage = sysinfo::System::global_cpu_usage(system);
    metrics.push(Metric::new(
        "cpu_usage_percent".to_string(),
        "cpu".to_string(),
        Value::Number(serde_json::Number::from_f64(global_cpu_usage as f64).unwrap()),
        HashMap::new(),
        Some("percent".to_string()),
    ));
    
    let load_avg = System::load_average();
    metrics.push(Metric::new(
        "load_average_1min".to_string(),
        "cpu".to_string(),
        Value::Number(serde_json::Number::from_f64(load_avg.one).unwrap_or(serde_json::Number::from(0))),
        HashMap::new(),
        None,
    ));

    metrics.push(Metric::new(
        "load_average_5min".to_string(),
        "cpu".to_string(),
        Value::Number(serde_json::Number::from_f64(load_avg.five).unwrap_or(serde_json::Number::from(0))),
        HashMap::new(),
        None,
    ));

    metrics.push(Metric::new(
        "load_average_15min".to_string(),
        "cpu".to_string(),
        Value::Number(serde_json::Number::from_f64(load_avg.fifteen).unwrap_or(serde_json::Number::from(0))),
        HashMap::new(),
        None,
    ));
    
    Ok(metrics)
}