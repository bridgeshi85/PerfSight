"""
CPU 分析器单元测试 (P2)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analyzers.cpu_analyzer import CPUAnalyzer


class TestCPUAnalyzer:
    """CPUAnalyzer 类测试"""

    @pytest.fixture
    def analyzer(self):
        """提供 CPUAnalyzer 实例"""
        return CPUAnalyzer()

    def _make_cpu_df(self, values, name='cpu_usage_percent'):
        """辅助方法: 构造 CPU DataFrame"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        return pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(len(values))],
            'name': [name] * len(values),
            'value': values,
        })

    def test_analyze_normal_cpu_data(self, analyzer):
        """TC-CA-01: 正常 CPU 数据统计正确"""
        # Arrange
        df = self._make_cpu_df([40.0, 45.0, 50.0, 55.0, 60.0])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'metrics' in result
        assert 'cpu_usage_percent' in result['metrics']
        stats = result['metrics']['cpu_usage_percent']['stats']
        assert stats['mean'] == 50.0
        assert stats['min'] == 40.0
        assert stats['max'] == 60.0

    def test_analyze_high_load_warning(self, analyzer):
        """TC-CA-02: mean>75 触发 warning insight"""
        # Arrange
        df = self._make_cpu_df([80.0, 85.0, 90.0, 75.0, 80.0])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'warning' in result['insights']
        assert 'CPU 负载偏高' in result['insights']['warning']

    def test_analyze_high_load_ratio(self, analyzer):
        """TC-CA-03: >80% 比例计算正确"""
        # Arrange - 10 个数据点，其中 3 个 > 80
        df = self._make_cpu_df([50.0, 60.0, 70.0, 75.0, 80.0, 81.0, 85.0, 90.0, 55.0, 65.0])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        high_load_ratio = result['metrics']['cpu_usage_percent']['high_load_ratio']
        assert high_load_ratio == 30.0  # 3/10 = 30%

    def test_analyze_empty_dataframe(self, analyzer):
        """TC-CA-04: 空数据返回空 metrics"""
        # Arrange
        df = pd.DataFrame(columns=['timestamp', 'name', 'value'])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert result['metrics'] == {}
        assert result['insights'] == {}

    def test_analyze_with_load_average(self, analyzer):
        """TC-CA-05: load_average 指标被处理"""
        # Arrange - 混合 cpu_usage_percent 和 load_average
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        df = pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(6)],
            'name': ['cpu_usage_percent'] * 3 + ['load_average_1min'] * 3,
            'value': [50.0, 60.0, 70.0, 2.5, 3.0, 2.8],
        })
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'cpu_usage_percent' in result['metrics']
        assert 'load_average_1min' in result['metrics']

    def test_analyze_no_cpu_usage_metric(self, analyzer):
        """TC-CA-06: 无 cpu_usage_percent 数据"""
        # Arrange - 只有 load_average
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        df = pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(3)],
            'name': ['load_average_1min'] * 3,
            'value': [2.5, 3.0, 2.8],
        })
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'cpu_usage_percent' not in result['metrics']
        assert 'load_average_1min' in result['metrics']
