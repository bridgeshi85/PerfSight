use anyhow::Result;
use std::collections::HashMap;
use serde_json::Value;
use sysinfo::{Disks};


use super::Metric;

pub struct DiskCollector {
    disks: Disks,
    target_disks: Vec<String>,
}

impl DiskCollector {
    pub fn new(target_disks: Vec<String>) -> Self {
        log::debug!("Initializing DiskCollector for disks: {:?}", target_disks);
        Self {
            disks: Disks::new_with_refreshed_list(),
            target_disks,
        }
    }

    pub fn collect(&mut self) -> Result<Vec<Metric>> {
        let mut metrics = Vec::new();

        self.disks.refresh(true);

        for disk in &self.disks {
            // 挂载点/盘符 (Windows: "C:\\"，Linux: "/"、"/data")，与配置字段 disk_mount_points 语义一致
            let mount_point = disk.mount_point().to_string_lossy().to_string();
            // 卷标 / 设备名 (Windows: 卷标签，Linux: "/dev/sda1")，仅作展示用途
            let disk_name = disk.name().to_string_lossy().to_string();

            // 如果指定了监控的磁盘，则按挂载点/盘符过滤
            if !self.target_disks.is_empty() && !self.target_disks.contains(&mount_point) {
                continue;
            }

            let mut labels = HashMap::new();
            labels.insert("disk".to_string(), mount_point.clone());
            labels.insert("disk_name".to_string(), disk_name.clone());

            let usage = disk.usage();
            // 距离上一次 collect() 被调用期间的字节数 (通常作为“速率”IO使用)
            let read_diff = usage.read_bytes;
            let written_diff = usage.written_bytes;

            // 这是自开机以来的总读写字节数 (仅作记录)
            let _total_read = usage.total_read_bytes;
            let _total_written = usage.total_written_bytes;

            log::debug!(
                "Disk [{} / {}]: Read {} B, Written {} B (since last check)",
                mount_point, disk_name, read_diff, written_diff
            );

            // 读取吞吐量
            metrics.push(Metric::new(
                "disk_read_bytes_per_sec".to_string(),
                "disk".to_string(),
                Value::Number(serde_json::Number::from(read_diff)),
                labels.clone(),
                Some("bytes/s".to_string()),
            ));

            // 写入吞吐量
            metrics.push(Metric::new(
                "disk_write_bytes_per_sec".to_string(),
                "disk".to_string(),
                Value::Number(serde_json::Number::from(written_diff)),
                labels.clone(),
                Some("bytes/s".to_string()),
            ));
        }

        log::debug!("✅ 成功采集磁盘指标: {} 个记录", metrics.len());
        Ok(metrics)
    }
}
