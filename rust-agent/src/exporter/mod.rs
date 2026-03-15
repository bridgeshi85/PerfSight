use anyhow::Result;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::str::FromStr;

use crate::collector::Metric;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ExportFormat {
    Json,
    Csv,
}

impl FromStr for ExportFormat {
    type Err = anyhow::Error;
    
    fn from_str(s: &str) -> Result<Self> {
        match s.to_lowercase().as_str() {
            "json" => Ok(ExportFormat::Json),
            "csv" => Ok(ExportFormat::Csv),
            _ => Err(anyhow::anyhow!("不支持的导出格式: {}", s)),
        }
    }
}

impl std::fmt::Display for ExportFormat {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ExportFormat::Json => write!(f, "json"),
            ExportFormat::Csv => write!(f, "csv"),
        }
    }
}

pub struct Exporter {
    output_dir: PathBuf,
    format: ExportFormat,
}

impl Exporter {
    pub fn new(output_dir: PathBuf, format: ExportFormat) -> Self {
        Self { output_dir, format }
    }
    
    pub async fn export(&self, metrics: &[Metric]) -> Result<()> {
        match self.format {
            ExportFormat::Json => self.export_json(metrics).await,
            ExportFormat::Csv => self.export_csv(metrics).await,
        }
    }
    
    async fn export_json(&self, metrics: &[Metric]) -> Result<()> {
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
        let filename = format!("perfsight_metrics_{}.json", timestamp);
        let filepath = self.output_dir.join(filename);
        
        let json_data = serde_json::to_string_pretty(metrics)?;
        tokio::fs::write(&filepath, json_data).await?;
        
        log::info!("指标已导出到: {:?}", filepath);
        Ok(())
    }
    
    async fn export_csv(&self, metrics: &[Metric]) -> Result<()> {
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
        let filename = format!("perfsight_metrics_{}.csv", timestamp);
        let filepath = self.output_dir.join(filename);
        
        let mut wtr = csv::Writer::from_path(&filepath)?;
        
        // 写入 CSV 头部
        wtr.write_record(&[
            "timestamp",
            "name", 
            "metric_type",
            "value",
            "labels",
            "unit"
        ])?;
        
        // 写入数据行
        for metric in metrics {
            let labels_str = serde_json::to_string(&metric.labels)?;
            let value_str = match &metric.value {
                serde_json::Value::Number(n) => n.to_string(),
                serde_json::Value::String(s) => s.clone(),
                serde_json::Value::Bool(b) => b.to_string(),
                other => serde_json::to_string(other)?,
            };
            
            wtr.write_record(&[
                metric.timestamp.to_rfc3339(),
                metric.name.clone(),
                metric.metric_type.clone(),
                value_str,
                labels_str,
                metric.unit.clone().unwrap_or_else(|| "".to_string()),
            ])?;
        }
        
        wtr.flush()?;
        log::info!("指标已导出到: {:?}", filepath);
        Ok(())
    }
    
    /// 清理过期的数据文件
    pub async fn cleanup_old_files(&self, retention_days: u32) -> Result<()> {
        let cutoff_time = Utc::now() - chrono::Duration::days(retention_days as i64);
        
        let mut entries = tokio::fs::read_dir(&self.output_dir).await?;
        while let Some(entry) = entries.next_entry().await? {
            let path = entry.path();
            if let Some(filename) = path.file_name() {
                if let Some(filename_str) = filename.to_str() {
                    if filename_str.starts_with("perfsight_metrics_") {
                        if let Ok(metadata) = entry.metadata().await {
                            if let Ok(created) = metadata.created() {
                                let created_time = chrono::DateTime::<Utc>::from(created);
                                if created_time < cutoff_time {
                                    if let Err(e) = tokio::fs::remove_file(&path).await {
                                        log::warn!("删除过期文件失败 {:?}: {}", path, e);
                                    } else {
                                        log::info!("已删除过期文件: {:?}", path);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        Ok(())
    }
}