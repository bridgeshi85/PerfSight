#[cfg(target_os = "linux")]
use procfs::KernelStats;

#[cfg(target_os = "linux")]
// 我们需要定义一个结构体来保存上一次的快照，以便计算差值
pub struct DeepCpuCollector {
    last_stats: Option<KernelStats>,
    last_time: std::time::Instant,
}

#[cfg(target_os = "linux")]
impl DeepCpuCollector {
    pub fn new() -> Self {
        Self {
            last_stats: None,
            last_time: std::time::Instant::now(),
        }
    }

    pub fn collect(&mut self) -> Result<Vec<crate::Metric>> {
        let mut metrics = Vec::new();

        // 读取当前内核状态
        let current_stats = KernelStats::new()?;
        let now = std::time::Instant::now();

        if let Some(last) = &self.last_stats {
            // 计算经过的时间 (秒)
            let elapsed_secs = now.duration_since(self.last_time).as_secs_f64();

            if elapsed_secs > 0.0 {
                // 1. 计算上下文切换率 (Context Switches Per Second)
                // ctxt 是开机以来的总上下文切换次数
                let cs_diff = current_stats.ctxt - last.ctxt;
                let cs_per_sec = cs_diff as f64 / elapsed_secs;

                let mut labels = HashMap::new();
                labels.insert("type".to_string(), "context_switches".to_string());

                metrics.push(crate::Metric::new(
                    "cpu_context_switches_rate".to_string(),
                    "rate".to_string(),
                    Value::Number(serde_json::Number::from_f64(cs_per_sec).unwrap_or(serde_json::Number::from(0))),
                    labels,
                    Some("switches/sec".to_string()),
                ));

                // 2. 计算用户态与内核态的时间差值 (进阶：计算百分比)
                // 注意：procfs 的 total 字段包含了 user, nice, system, idle, iowait 等 tick 数
                let user_diff = current_stats.total.user - last.total.user;
                let system_diff = current_stats.total.system - last.total.system;
                let idle_diff = current_stats.total.idle - last.total.idle;
                let iowait_diff = current_stats.total.iowait.unwrap_or(0) - last.total.iowait.unwrap_or(0);

                let total_ticks_diff = user_diff + system_diff + idle_diff + iowait_diff; // 简化的总 tick

                if total_ticks_diff > 0 {
                    let user_percent = (user_diff as f64 / total_ticks_diff as f64) * 100.0;
                    let system_percent = (system_diff as f64 / total_ticks_diff as f64) * 100.0;
                    let iowait_percent = (iowait_diff as f64 / total_ticks_diff as f64) * 100.0;

                    let mut cpu_details = serde_json::Map::new();
                    cpu_details.insert("user_percent".to_string(), Value::Number(serde_json::Number::from_f64(user_percent).unwrap()));
                    cpu_details.insert("system_percent".to_string(), Value::Number(serde_json::Number::from_f64(system_percent).unwrap()));
                    cpu_details.insert("iowait_percent".to_string(), Value::Number(serde_json::Number::from_f64(iowait_percent).unwrap()));

                    metrics.push(crate::Metric::new(
                        "cpu_deep_metrics".to_string(),
                        "cpu_details".to_string(),
                        Value::Object(cpu_details),
                        HashMap::new(),
                        Some("percent".to_string()),
                    ));
                }
            }
        }

        // 更新快照，留给下一次循环使用
        self.last_stats = Some(current_stats);
        self.last_time = now;

        Ok(metrics)
    }
}