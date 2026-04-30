import logging
from typing import Dict, Any
import pandas as pd
from analyzers.base_analyzer import BaseMetricAnalyzer

logger = logging.getLogger(__name__)


class CPUAnalyzer(BaseMetricAnalyzer):
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        result = {'metrics': {}, 'insights': {}}
        # 1. 核心 CPU 使用率分析
        cpu_percent_df = df[df['name'] == 'cpu_usage_percent']
        if not cpu_percent_df.empty:
            s = cpu_percent_df['value']
            stats = self.calculate_basic_stats(s)
            numeric_s = pd.to_numeric(s, errors='coerce').dropna()

            result['metrics']['cpu_usage_percent'] = {
                'stats': stats,
                'trend': self.calculate_trend(s),
                'anomalies': self.detect_anomalies_iqr(s),
                'high_load_ratio': float((numeric_s > 80.0).mean() * 100)  # 业务规则：计算超载比例
            }

            if stats.get('mean', 0) > 75.0:
                result['insights']['warning'] = "整体 CPU 负载偏高，存在性能瓶颈风险"

        # 2. 附带分析 Load Average
        for load_metric in ['load_average_1min', 'load_average_5min']:
            load_df = df[df['name'] == load_metric]
            if not load_df.empty:
                result['metrics'][load_metric] = {
                    'stats': self.calculate_basic_stats(load_df['value'])
                }
        return result
