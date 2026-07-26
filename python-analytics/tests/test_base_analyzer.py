"""
基础分析器单元测试 (P0)
"""
import pytest
import pandas as pd
import numpy as np
from analyzers.base_analyzer import BaseMetricAnalyzer


class TestCalculateBasicStats:
    """calculate_basic_stats 方法测试"""

    def test_calculate_basic_stats_normal(self, sample_numeric_series):
        """TC-BA-01: 正常数值序列的统计计算"""
        # Arrange & Act
        stats = BaseMetricAnalyzer.calculate_basic_stats(sample_numeric_series)
        
        # Assert
        assert 'mean' in stats
        assert 'median' in stats
        assert 'max' in stats
        assert 'min' in stats
        assert 'std' in stats
        assert 'q25' in stats
        assert 'q75' in stats
        
        # 验证计算正确性
        assert stats['mean'] == 30.0
        assert stats['median'] == 30.0
        assert stats['max'] == 50.0
        assert stats['min'] == 10.0

    def test_calculate_basic_stats_empty_series(self, sample_empty_series):
        """TC-BA-02: 空 Series 返回空 dict"""
        # Arrange & Act
        stats = BaseMetricAnalyzer.calculate_basic_stats(sample_empty_series)
        
        # Assert
        assert stats == {}

    def test_calculate_basic_stats_with_nan(self, sample_series_with_nan):
        """TC-BA-03: 含 NaN 的序列自动跳过"""
        # Arrange & Act
        stats = BaseMetricAnalyzer.calculate_basic_stats(sample_series_with_nan)
        
        # Assert - NaN 被跳过，只计算有效值
        assert stats['mean'] == 20.0  # (10+20+30)/3
        assert stats['median'] == 20.0

    def test_calculate_basic_stats_single_value(self):
        """TC-BA-11: 单值序列"""
        # Arrange
        series = pd.Series([42.0])
        
        # Act
        stats = BaseMetricAnalyzer.calculate_basic_stats(series)
        
        # Assert
        assert stats['mean'] == 42.0
        # pandas std() 返回 NaN 对单值（样本标准差 ddof=1）
        assert pd.isna(stats['std']) or stats['std'] == 0.0

    def test_calculate_basic_stats_all_same(self):
        """TC-BA-12: 全部相同值 std=0"""
        # Arrange
        series = pd.Series([10.0, 10.0, 10.0, 10.0])
        
        # Act
        stats = BaseMetricAnalyzer.calculate_basic_stats(series)
        
        # Assert
        assert stats['mean'] == 10.0
        assert stats['std'] == 0.0


class TestDetectAnomaliesIQR:
    """detect_anomalies_iqr 方法测试"""

    def test_detect_anomalies_iqr_no_anomalies(self):
        """TC-BA-04: 均匀数据无异常点"""
        # Arrange - 均匀分布数据
        series = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        
        # Act
        result = BaseMetricAnalyzer.detect_anomalies_iqr(series)
        
        # Assert
        assert result['count'] == 0
        assert result['percentage'] == 0.0

    def test_detect_anomalies_iqr_with_outliers(self, sample_series_with_outliers):
        """TC-BA-05: 注入极端值后检测到异常"""
        # Arrange - fixture 包含 [10, 12, 11, 13, 12, 100, 5]
        
        # Act
        result = BaseMetricAnalyzer.detect_anomalies_iqr(sample_series_with_outliers)
        
        # Assert - 应该检测到 100 和 5 为异常值
        assert result['count'] > 0
        assert result['percentage'] > 0
        assert 'lower_bound' in result
        assert 'upper_bound' in result

    def test_detect_anomalies_iqr_empty_series(self, sample_empty_series):
        """TC-BA-06: 空序列返回 count=0"""
        # Arrange & Act
        result = BaseMetricAnalyzer.detect_anomalies_iqr(sample_empty_series)
        
        # Assert
        assert result['count'] == 0
        assert result['percentage'] == 0.0

    def test_detect_anomalies_iqr_zero_std(self):
        """TC-BA-07: 标准差为 0 时安全返回"""
        # Arrange - 所有值相同
        series = pd.Series([10.0, 10.0, 10.0, 10.0])
        
        # Act
        result = BaseMetricAnalyzer.detect_anomalies_iqr(series)
        
        # Assert - std=0 时应安全返回
        assert result['count'] == 0
        assert result['percentage'] == 0.0


class TestCalculateTrend:
    """calculate_trend 方法测试"""

    def test_calculate_trend_increasing(self, sample_increasing_series):
        """TC-BA-08: 上升趋势检测"""
        # Arrange & Act
        result = BaseMetricAnalyzer.calculate_trend(sample_increasing_series)
        
        # Assert
        assert result['direction'] == 'increasing'
        assert result['slope'] > 0
        assert result['r_squared'] > 0.9  # 完美线性增长

    def test_calculate_trend_decreasing(self, sample_decreasing_series):
        """TC-BA-09: 下降趋势检测"""
        # Arrange & Act
        result = BaseMetricAnalyzer.calculate_trend(sample_decreasing_series)
        
        # Assert
        assert result['direction'] == 'decreasing'
        assert result['slope'] < 0
        assert result['r_squared'] > 0.9

    def test_calculate_trend_insufficient_data(self):
        """TC-BA-10: 少于 2 个点返回空 dict"""
        # Arrange - 只有 1 个数据点
        series = pd.Series([10.0])
        
        # Act
        result = BaseMetricAnalyzer.calculate_trend(series)
        
        # Assert
        assert result == {}

    def test_calculate_trend_stable(self):
        """TC-BA-10 补充: 稳定趋势检测"""
        # Arrange - 所有值相同
        series = pd.Series([10.0, 10.0, 10.0, 10.0])
        
        # Act
        result = BaseMetricAnalyzer.calculate_trend(series)
        
        # Assert
        assert result['direction'] == 'stable'
        assert abs(result['slope']) < 0.001  # 斜率接近 0
