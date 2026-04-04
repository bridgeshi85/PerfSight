use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::{NetworkData, Networks};

use super::Metric;

pub fn collect_network_metrics(interfaces: &[String]) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();
    let networks = Networks::new_with_refreshed_list();

    for (interface_name, data) in &networks {
        // 如果指定了监控的网络接口，则只监控指定的
        if !interfaces.is_empty() && !interfaces.contains(interface_name) {
            continue;
        }
        
        let mut labels = HashMap::new();
        labels.insert("interface".to_string(), interface_name.to_string());
        
        // 网络接口详情
        let mut network_details = serde_json::Map::new();
        network_details.insert("received_bytes".to_string(), Value::Number(serde_json::Number::from(NetworkData::received(data))));
        network_details.insert("transmitted_bytes".to_string(), Value::Number(serde_json::Number::from(NetworkData::transmitted(data))));
        network_details.insert("packets_received".to_string(), Value::Number(serde_json::Number::from(NetworkData::packets_received(data))));
        network_details.insert("packets_transmitted".to_string(), Value::Number(serde_json::Number::from(NetworkData::packets_transmitted(data))));

        metrics.push(Metric::new(
            "network_interface".to_string(),
            "network_interface".to_string(),
            Value::Object(network_details),
            labels.clone(),
            None,
        ));
        
        // 单独的网络指标
        metrics.push(Metric::new(
            "network_received_bytes".to_string(),
            "network_received".to_string(),
            Value::Number(serde_json::Number::from(NetworkData::received(data))),
            labels.clone(),
            Some("bytes".to_string()),
        ));
        
        metrics.push(Metric::new(
            "network_transmitted_bytes".to_string(),
            "network_transmitted".to_string(),
            Value::Number(serde_json::Number::from(NetworkData::transmitted(data))),
            labels,
            Some("bytes".to_string()),
        ));
    }
    
    Ok(metrics)
}