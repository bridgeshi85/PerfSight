import logging
from typing import Dict, Any
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


# ==========================================
# 基础分析器 (提供通用的统计和算法能力)
# ==========================================
class BaseMetricAnalyzer:
    def __init__(self, config=None):
        self.config = config

    @staticmethod
    def calculate_basic_stats(series: pd.Series) -> Dict[str, float]:
        """通用的数值序列统计计算"""
        s = pd.to_numeric(series, errors='coerce').dropna()
        if s.empty:
            return {}
        return {
            'mean': float(s.mean()),
            'median': float(s.median()),
            'max': float(s.max()),
            'min': float(s.min()),
            'std': float(s.std()),
            'q25': float(s.quantile(0.25)),
            'q75': float(s.quantile(0.75))
        }

    @staticmethod
    def detect_anomalies_iqr(series: pd.Series) -> Dict[str, Any]:
        """通用的 IQR 异常检测"""
        s = pd.to_numeric(series, errors='coerce').dropna()
        if s.empty or s.std() == 0:
            return {'count': 0, 'percentage': 0.0}

        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomalies = s[(s < lower_bound) | (s > upper_bound)]
        return {
            'count': int(len(anomalies)),
            'percentage': float(len(anomalies) / len(s) * 100),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound)
        }

    @staticmethod
    def calculate_trend(series: pd.Series) -> Dict[str, Any]:
        """通用的线性回归趋势计算"""
        s = pd.to_numeric(series, errors='coerce').dropna()
        if len(s) < 2:
            return {}

        x = np.arange(len(s))
        slope, _, r_value, p_value, _ = stats.linregress(x, s)
        return {
            'slope': float(slope),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
        }
