import logging
from typing import Dict, Any
import pandas as pd
from .base_analyzer import BaseMetricAnalyzer

logger = logging.getLogger(__name__)


class MemoryAnalyzer(BaseMetricAnalyzer):
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        result = {'metrics': {}, 'insights': {}}

        # 针对内存使用率
        mem_percent_df = df[df['name'] == 'memory_used_percent']
        if not mem_percent_df.empty:
            s = mem_percent_df['value']
            stats = self.calculate_basic_stats(s)
            numeric_s = pd.to_numeric(s, errors='coerce').dropna()

            result['metrics']['memory_used_percent'] = {
                'stats': stats,
                'trend': self.calculate_trend(s),
                'anomalies': self.detect_anomalies_iqr(s),
                'oom_risk_ratio': float((numeric_s > 90.0).mean() * 100)  # 业务规则：计算 OOM 风险
            }

            trend = self.calculate_trend(s)
            if trend.get('direction') == 'increasing' and trend.get('r_squared', 0) > 0.7:
                result['insights']['critical'] = "发现强烈的内存泄漏(Memory Leak)特征趋势"

        return result
