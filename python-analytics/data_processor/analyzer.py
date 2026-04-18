"""
数据分析模块
负责对清洗后的性能数据进行统计分析和模式识别
"""

import logging
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
    
    async def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """执行完整的数据分析"""
        if df.empty:
            return {}
        
        logger.info("开始数据分析...")
        
        results = {
            'summary': await self._basic_statistics(df),
            'trends': await self._trend_analysis(df),
            'anomalies': await self._anomaly_detection(df),
            'correlations': await self._correlation_analysis(df),
            'performance_metrics': await self._performance_metrics(df),
            'time_patterns': await self._time_pattern_analysis(df),
        }
        
        logger.info("数据分析完成")
        return results
    
    async def _basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """基础统计分析"""
        stats_result = {
            'total_records': len(df),
            'time_range': {},
            'metric_types': {},
            'numeric_stats': {}
        }
        
        # 时间范围分析
        if 'timestamp' in df.columns:
            stats_result['time_range'] = {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat(),
                'duration_hours': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
            }
        
        # 指标类型分布
        if 'metric_type' in df.columns:
            type_counts = df['metric_type'].value_counts()
            stats_result['metric_types'] = type_counts.to_dict()
        
        # 数值列统计
        # Todo - 只根据type进行统计是不合理的，因为type中会有不同的name每个name不能被一起计算
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in df.columns:
                stats_result['numeric_stats'][col] = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'q25': float(df[col].quantile(0.25)),
                    'q75': float(df[col].quantile(0.75))
                }
        
        return stats_result
    
    async def _trend_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """趋势分析"""
        trends = {}
        
        if 'timestamp' not in df.columns:
            return trends
        
        # 按指标类型分组分析趋势
        if 'metric_type' in df.columns:
            for metric_type in df['metric_type'].unique():
                metric_data = df[df['metric_type'] == metric_type]
                
                if len(metric_data) > 2:
                    trends[metric_type] = await self._calculate_trend(metric_data)
        
        return trends
    
    async def _calculate_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算单个指标的趋势"""
        if 'value_parsed' in df.columns:
            values = pd.to_numeric(df['value_parsed'], errors='coerce').dropna()
        elif 'value' in df.columns:
            values = pd.to_numeric(df['value'], errors='coerce').dropna()
        else:
            return {}
        
        if len(values) < 2:
            return {}
        
        # 线性回归分析趋势
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        return {
            'slope': float(slope),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
            'trend_strength': 'strong' if abs(r_value) > 0.7 else 'moderate' if abs(r_value) > 0.3 else 'weak'
        }
    
    async def _anomaly_detection(self, df: pd.DataFrame) -> Dict[str, Any]:
        """异常检测"""
        anomalies = {
            'total_anomalies': 0,
            'anomaly_details': []
        }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in df.columns and df[col].std() > 0:
                # 使用 IQR 方法检测异常值
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                anomaly_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                anomaly_count = anomaly_mask.sum()
                
                if anomaly_count > 0:
                    anomalies['total_anomalies'] += anomaly_count
                    anomalies['anomaly_details'].append({
                        'column': col,
                        'count': int(anomaly_count),
                        'percentage': float(anomaly_count / len(df) * 100),
                        'lower_bound': float(lower_bound),
                        'upper_bound': float(upper_bound)
                    })
        
        return anomalies
    
    async def _correlation_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """相关性分析"""
        correlations = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            
            # 找出强相关性（绝对值 > 0.7）
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:
                        strong_correlations.append({
                            'var1': corr_matrix.columns[i],
                            'var2': corr_matrix.columns[j],
                            'correlation': float(corr_value),
                            'strength': 'strong positive' if corr_value > 0.7 else 'strong negative'
                        })
            
            correlations = {
                'correlation_matrix': corr_matrix.to_dict(),
                'strong_correlations': strong_correlations
            }
        
        return correlations
    
    async def _performance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """性能指标分析"""
        metrics = {}
        
        # CPU 使用率分析
        cpu_data = df[df['metric_type'] == 'cpu_usage']
        if not cpu_data.empty:
            metrics['cpu'] = await self._analyze_cpu_metrics(cpu_data)
        
        # 内存使用率分析
        memory_data = df[df['metric_type'] == 'memory_usage']
        if not memory_data.empty:
            metrics['memory'] = await self._analyze_memory_metrics(memory_data)
        
        # 磁盘使用率分析
        disk_data = df[df['metric_type'] == 'disk_usage']
        if not disk_data.empty:
            metrics['disk'] = await self._analyze_disk_metrics(disk_data)
        
        return metrics
    
    async def _analyze_cpu_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析 CPU 指标"""
        if 'value_parsed' in df.columns:
            cpu_values = pd.to_numeric(df['value_parsed'], errors='coerce').dropna()
        else:
            cpu_values = pd.to_numeric(df['value'], errors='coerce').dropna()
        
        if cpu_values.empty:
            return {}
        
        return {
            'avg_usage': float(cpu_values.mean()),
            'max_usage': float(cpu_values.max()),
            'min_usage': float(cpu_values.min()),
            'high_usage_percentage': float((cpu_values > 80).sum() / len(cpu_values) * 100),
            'usage_volatility': float(cpu_values.std())
        }
    
    async def _analyze_memory_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析内存指标"""
        # 简化的内存分析
        return {
            'analysis_type': 'memory',
            'records_count': len(df)
        }
    
    async def _analyze_disk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析磁盘指标"""
        # 简化的磁盘分析
        return {
            'analysis_type': 'disk',
            'records_count': len(df)
        }
    
    async def _time_pattern_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """时间模式分析"""
        patterns = {}
        
        if 'timestamp' not in df.columns:
            return patterns
        
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # 按小时统计
        hourly_stats = df.groupby('hour').size()
        patterns['hourly_distribution'] = hourly_stats.to_dict()
        
        # 按星期统计
        weekly_stats = df.groupby('day_of_week').size()
        patterns['weekly_distribution'] = weekly_stats.to_dict()
        
        # 找出高峰时段
        peak_hour = hourly_stats.idxmax()
        patterns['peak_hour'] = int(peak_hour)
        patterns['peak_hour_count'] = int(hourly_stats.max())
        
        return patterns