use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;
use sysinfo::{Disk, Disks};


use super::Metric;

pub fn collect_disk_metrics(mount_points: &[String]) -> Result<Vec<Metric>> {
    let mut metrics = Vec::new();

    // 初始化并获取最新的磁盘列表
    let disks = Disks::new_with_refreshed_list();
    
    for disk in disks.list() {
        let mount_point = Disk::mount_point(&disk).to_string_lossy().to_string();
        
        // 如果指定了监控的挂载点，则只监控指定的
        if !mount_points.is_empty() && !mount_points.contains(&mount_point) {
            continue;
        }
        
        let mut labels = HashMap::new();
        labels.insert("mount_point".to_string(), mount_point.clone());
        labels.insert("file_system".to_string(), Disk::file_system(&disk).to_string_lossy().to_string());
        labels.insert("disk_name".to_string(), Disk::name(&disk).to_string_lossy().to_string());
        
        let total_space = disk.total_space();
        let available_space = disk.available_space();
        let used_space = total_space - available_space;
        
        let used_percent = if total_space > 0 {
            (used_space as f64 / total_space as f64) * 100.0
        } else {
            0.0
        };
        
        // 磁盘使用详情
        let mut disk_details = serde_json::Map::new();
        disk_details.insert("total_bytes".to_string(), Value::Number(serde_json::Number::from(total_space)));
        disk_details.insert("used_bytes".to_string(), Value::Number(serde_json::Number::from(used_space)));
        disk_details.insert("available_bytes".to_string(), Value::Number(serde_json::Number::from(available_space)));
        disk_details.insert("used_percent".to_string(), Value::Number(serde_json::Number::from_f64(used_percent).unwrap()));
        
        metrics.push(Metric::new(
            "disk_usage".to_string(),
            "disk".to_string(),
            Value::Object(disk_details),
            labels.clone(),
            None,
        ));
        
        // 单独的磁盘指标
        metrics.push(Metric::new(
            "disk_total_bytes".to_string(),
            "disk".to_string(),
            Value::Number(serde_json::Number::from(total_space)),
            labels.clone(),
            Some("bytes".to_string()),
        ));
        
        metrics.push(Metric::new(
            "disk_used_bytes".to_string(),
            "disk".to_string(),
            Value::Number(serde_json::Number::from(used_space)),
            labels.clone(),
            Some("bytes".to_string()),
        ));
        
        metrics.push(Metric::new(
            "disk_used_percent".to_string(),
            "disk".to_string(),
            Value::Number(serde_json::Number::from_f64(used_percent).unwrap()),
            labels.clone(),
            Some("percent".to_string()),
        ));
        
        metrics.push(Metric::new(
            "disk_available_bytes".to_string(),
            "disk".to_string(),
            Value::Number(serde_json::Number::from(available_space)),
            labels,
            Some("bytes".to_string()),
        ));
    }
    
    Ok(metrics)
}