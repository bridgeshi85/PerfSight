use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::{NetworkData, Networks};

use super::Metric;

pub fn collect_network_metrics(interfaces: &[String]) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();
    let networks = Networks::new_with_refreshed_list();

    log::debug!("Collecting network metrics for interfaces: {:?}", interfaces);

    for (interface_name, data) in &networks {
        // 如果指定了监控的网络接口，则只监控指定的
        if !interfaces.is_empty() && !interfaces.contains(interface_name) {
            continue;
        }
        
        let mut labels = HashMap::new();
        labels.insert("interface".to_string(), interface_name.to_string());

        // 先把数据提取出来，方便日志打印
        let rx_bytes = NetworkData::received(data);
        let tx_bytes = NetworkData::transmitted(data);
        let rx_packets = NetworkData::packets_received(data);
        let tx_packets = NetworkData::packets_transmitted(data);

        // 扁平化网络指标
        metrics.push(Metric::new(
            "network_received_bytes".to_string(),
            "network".to_string(),
            Value::Number(serde_json::Number::from(rx_bytes)),
            labels.clone(),
            Some("bytes".to_string()),
        ));
        
        metrics.push(Metric::new(
            "network_transmitted_bytes".to_string(),
            "network".to_string(),
            Value::Number(serde_json::Number::from(tx_bytes)),
            labels.clone(),
            Some("bytes".to_string()),
        ));

        metrics.push(Metric::new(
            "network_received_packets".to_string(),
            "network".to_string(),
            Value::Number(serde_json::Number::from(rx_packets)),
            labels.clone(),
            Some("count".to_string()),
        ));

        metrics.push(Metric::new(
            "network_transmitted_packets".to_string(),
            "network".to_string(),
            Value::Number(serde_json::Number::from(tx_packets)),
            labels,
            Some("count".to_string()),
        ));

        log::debug!(
            "✅ 成功采集收集指标: [{:?}]",
            metrics
        );
    }
    
    Ok(metrics)
}