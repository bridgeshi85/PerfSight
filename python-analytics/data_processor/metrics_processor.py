import logging
from typing import Dict, Any
import pandas as pd
from analyzers.base_analyzer import BaseMetricAnalyzer
from analyzers.cpu_analyzer import CPUAnalyzer
from analyzers.memory_analyzer import MemoryAnalyzer
from analyzers.network_analyzer import NetworkAnalyzer


logger = logging.getLogger(__name__)


class MetricsProcessor:
    """指标处理调度引擎 (负责路由分发和结果聚合)"""

    def __init__(self, config=None):
        self.config = config
        # 注册分析器路由表 (Registry)
        self.analyzers = {
            'cpu': CPUAnalyzer(config),
            'memory': MemoryAnalyzer(config),
            'network': NetworkAnalyzer(config)
        }

    async def process(self, df: pd.DataFrame) -> Dict[str, Any]:
        """执行完整的指标处理流水线"""
        if df.empty: return {}
        logger.info("开始执行指标专项处理与分析...")

        # 1. 提取大盘全局信息
        results = {
            'summary': {
                'total_records': len(df),
                'time_range': {
                    'start': df['timestamp'].min() if 'timestamp' in df.columns else None,
                    'end': df['timestamp'].max() if 'timestamp' in df.columns else None
                }
            },
            'categories': {}
        }

        # 根据指标类型分发给不同的analyzers进行处理
        if 'metric_type' in df.columns:
            for m_type in df['metric_type'].unique():
                if m_type in self.analyzers:
                    # 将属于该类别的数据切片
                    type_df = df[df['metric_type'] == m_type].copy()
                    results['categories'][m_type] = self.analyzers[m_type].analyze(type_df)
                else:
                    logger.debug(f"未找到针对 '{m_type}' 类型的专属分析器，已跳过。")

        logger.info("指标专项处理与分析完成")
        return results
