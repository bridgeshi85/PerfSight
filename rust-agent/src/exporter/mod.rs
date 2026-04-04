use anyhow::Result;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::str::FromStr;
use tokio::io::AsyncWriteExt;
use crate::collector::Metric;
use std::sync::atomic::{AtomicBool, Ordering};

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
    format: ExportFormat,
    filepath: PathBuf,
    is_first_write: AtomicBool,
}

impl Exporter {
    pub fn new(output_dir: PathBuf, format: ExportFormat) -> Self {
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
        let ext = match format {
            ExportFormat::Json => "jsonl",
            ExportFormat::Csv => "csv",
        };
        let filename = format!("perfsight_run_{}.{}", timestamp, ext);
        let filepath = output_dir.join(filename);

        log::info!("压测数据将流式写入文件: {:?}", filepath);

        Self {
            format,
            filepath,
            is_first_write: AtomicBool::new(true)
        }
    }
    
    pub async fn export(&self, metrics: &[Metric]) -> Result<()> {
        match self.format {
            ExportFormat::Json => self.export_json(metrics).await,
            ExportFormat::Csv => self.export_csv(metrics).await,
        }
    }
    
    async fn export_json(&self, metrics: &[Metric]) -> Result<()> {
        let mut file = tokio::fs::OpenOptions::new().
            create(true).append(true).open(&self.filepath).await?;

        let mut buffer = String::with_capacity(metrics.len() * 256); // 预分配内存，提升速度
        for metric in metrics {
            let json_line = serde_json::to_string(metric)?; // 转为紧凑的单行
            buffer.push_str(&json_line);
            buffer.push('\n'); // 追加换行符
        }

        file.write_all(buffer.as_bytes()).await?;
        log::debug!("追加了 {} 条指标到 JSONL", metrics.len());
        Ok(())
    }
    
    async fn export_csv(&self, metrics: &[Metric]) -> Result<()> {
        let mut file = tokio::fs::OpenOptions::new().
            append(true).create(true).open(&self.filepath).await?;
        let mut buffer = String::with_capacity(metrics.len() * 256);

        // 写入header后会自动swap成false
        if self.is_first_write.swap(false, Ordering::SeqCst) {
            buffer.push_str("timestamp,name,metric_type,value,labels,unit\n");
        }

        // 写入数据行
        for metric in metrics {
            let labels_str = serde_json::to_string(&metric.labels)?.replace("\"", "\"\"");
            let value_str = match &metric.value {
                serde_json::Value::Number(n) => n.to_string(),
                serde_json::Value::String(s) => s.clone(),
                serde_json::Value::Bool(b) => b.to_string(),
                other => serde_json::to_string(other)?,
            };

            let line = format!(
                "{},\"{}\",\"{}\",\"{}\",\"{}\",\"{}\"\n",
                metric.timestamp.to_rfc3339(),
                metric.name,
                metric.metric_type,
                value_str,
                labels_str,
                metric.unit.as_deref().unwrap_or("")
            );
            
            buffer.push_str(&line);
        }

        file.write_all(buffer.as_bytes()).await?;

        log::debug!("追加了 {} 条指标到 CSV", metrics.len());
        Ok(())
    }
}