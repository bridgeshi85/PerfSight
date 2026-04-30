use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::{NetworkData, Networks};

use super::Metric;

// 定义一个带有状态的收集器结构体
pub struct NetworkCollector {
    networks: Networks,
    target_interfaces: Vec<String>,
}

impl NetworkCollector {
    pub fn new(target_interfaces: Vec<String>) -> Self {
        log::info!("Initializing NetworkCollector for interfaces: {:?}", target_interfaces);
        Self {
            networks: Networks::new_with_refreshed_list(),
            target_interfaces,
        }
    }

    pub fn collect(&mut self) -> Result<Vec<Metric>> {

        let mut metrics = Vec::new();
        self.networks.refresh(true);

        log::debug!("Collecting network metrics for interfaces: {:?}", self.target_interfaces);

        for (interface_name, data) in &self.networks {
            // 如果指定了监控的网络接口，则只监控指定的
            if !self.target_interfaces.is_empty() && !self.target_interfaces.contains(interface_name) {
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
}