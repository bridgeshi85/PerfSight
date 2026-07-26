"""
Memory 分析器单元测试 (P2)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analyzers.memory_analyzer import MemoryAnalyzer


class TestMemoryAnalyzer:
    """MemoryAnalyzer 类测试"""

    @pytest.fixture
    def analyzer(self):
        """提供 MemoryAnalyzer 实例"""
        return MemoryAnalyzer()

    def _make_mem_df(self, values, col='value'):
        """辅助方法: 构造 Memory DataFrame"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        data = {
            'timestamp': [base_time + timedelta(minutes=i) for i in range(len(values))],
            'name': ['memory_used_percent'] * len(values),
            'value': values,
        }
        if col == 'value_parsed':
            data['value_parsed'] = values
        return pd.DataFrame(data)

    def test_analyze_normal_memory(self, analyzer):
        """TC-MA-01: 正常内存数据统计"""
        # Arrange
        df = self._make_mem_df([50.0, 55.0, 60.0, 65.0, 70.0])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'memory_used_percent' in result['metrics']
        stats = result['metrics']['memory_used_percent']['stats']
        assert stats['mean'] == 60.0
        assert stats['min'] == 50.0
        assert stats['max'] == 70.0

    def test_analyze_oom_risk_ratio(self, analyzer):
        """TC-MA-02: >90% 的 OOM 风险比例"""
        # Arrange - 10 个点，3 个 > 90
        df = self._make_mem_df([60.0, 70.0, 80.0, 85.0, 88.0, 91.0, 93.0, 95.0, 75.0, 65.0])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        oom_risk = result['metrics']['memory_used_percent']['oom_risk_ratio']
        assert oom_risk == 30.0  # 3/10 = 30%

    def test_analyze_memory_leak_detection(self, analyzer):
        """TC-MA-03: 上升趋势+r²>0.7 触发 critical"""
        # Arrange - 持续上升的内存使用
        df = self._make_mem_df([40.0, 50.0, 60.0, 70.0, 80.0, 85.0, 90.0])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'critical' in result['insights']
        assert '内存泄漏' in result['insights']['critical']

    def test_analyze_empty_dataframe(self, analyzer):
        """TC-MA-04: 空数据返回空结果"""
        # Arrange
        df = pd.DataFrame(columns=['timestamp', 'name', 'value'])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert result['metrics'] == {}
        assert result['insights'] == {}

    def test_analyze_uses_value_parsed(self, analyzer):
        """TC-MA-05: 优先使用 value_parsed 列"""
        # Arrange - 同时有 value 和 value_parsed
        df = self._make_mem_df([50.0, 60.0, 70.0], col='value_parsed')
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert - 应该使用 value_parsed 列的数据
        stats = result['metrics']['memory_used_percent']['stats']
        assert stats['mean'] == 60.0
