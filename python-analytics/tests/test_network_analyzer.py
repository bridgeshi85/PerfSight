"""
Network 分析器单元测试 (P2)
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from analyzers.network_analyzer import NetworkAnalyzer


class TestNetworkAnalyzer:
    """NetworkAnalyzer 类测试"""

    @pytest.fixture
    def analyzer(self):
        """提供 NetworkAnalyzer 实例"""
        return NetworkAnalyzer()

    def _make_net_df(self, names, values):
        """辅助方法: 构造 Network DataFrame"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        return pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(len(values))],
            'name': names,
            'value': values,
        })

    def test_analyze_rx_tx_data(self, analyzer):
        """TC-NA-01: 收发字节数据统计"""
        # Arrange
        names = ['network_received_bytes'] * 3 + ['network_transmitted_bytes'] * 3
        values = [1024, 2048, 3072, 512, 1024, 1536]
        df = self._make_net_df(names, values)
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'network_received_bytes' in result['metrics']
        assert 'network_transmitted_bytes' in result['metrics']
        rx_stats = result['metrics']['network_received_bytes']['stats']
        assert rx_stats['mean'] == 2048.0

    def test_analyze_empty_dataframe(self, analyzer):
        """TC-NA-02: 空数据返回空"""
        # Arrange
        df = pd.DataFrame(columns=['timestamp', 'name', 'value'])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert result['metrics'] == {}

    def test_analyze_only_rx(self, analyzer):
        """TC-NA-03: 仅有接收数据"""
        # Arrange
        names = ['network_received_bytes'] * 3
        values = [1024, 2048, 3072]
        df = self._make_net_df(names, values)
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'network_received_bytes' in result['metrics']
        assert 'network_transmitted_bytes' not in result['metrics']

    def test_analyze_only_tx(self, analyzer):
        """TC-NA-04: 仅有发送数据"""
        # Arrange
        names = ['network_transmitted_bytes'] * 3
        values = [512, 1024, 1536]
        df = self._make_net_df(names, values)
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'network_transmitted_bytes' in result['metrics']
        assert 'network_received_bytes' not in result['metrics']
