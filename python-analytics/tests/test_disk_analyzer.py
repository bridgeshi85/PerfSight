"""
Disk 分析器单元测试 (P2)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analyzers.disk_analyzer import DiskAnalyzer


class TestDiskAnalyzer:
    """DiskAnalyzer 类测试"""

    @pytest.fixture
    def analyzer(self):
        """提供 DiskAnalyzer 实例"""
        return DiskAnalyzer()

    def _make_disk_df(self, disk_name, read_values, write_values):
        """辅助方法: 构造 Disk DataFrame"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        n_read = len(read_values)
        n_write = len(write_values)
        total = n_read + n_write
        
        labels_str = f'{{"disk": "{disk_name}"}}'
        labels_dict = {'disk': disk_name}
        
        return pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(total)],
            'metric_type': ['disk'] * total,
            'name': ['disk_read_bytes_per_sec'] * n_read + ['disk_write_bytes_per_sec'] * n_write,
            'value': read_values + write_values,
            'labels': [labels_str] * total,
            'labels_parsed': [labels_dict] * total,
        })

    def test_analyze_normal_disk_io(self, analyzer):
        """TC-DA-01: 正常磁盘读写分析"""
        # Arrange - 10 MB/s 读, 5 MB/s 写
        mb = 1024 * 1024
        df = self._make_disk_df('sda',
                                [10*mb, 12*mb, 11*mb],
                                [5*mb, 6*mb, 4*mb])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'disks' in result['metrics']
        assert 'sda' in result['metrics']['disks']
        disk_stats = result['metrics']['disks']['sda']
        assert 'read' in disk_stats
        assert 'write' in disk_stats
        # 读取均值约 11 MB/s
        assert disk_stats['read']['stats']['mean'] > 9

    def test_analyze_empty_dataframe(self, analyzer):
        """TC-DA-02: 空数据返回 summary"""
        # Arrange
        df = pd.DataFrame()
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert result['metrics'] == {}
        assert result['insights'] == {}

    def test_analyze_high_read_warning(self, analyzer):
        """TC-DA-03: 平均读>100MB/s 触发告警"""
        # Arrange
        mb = 1024 * 1024
        df = self._make_disk_df('nvme0',
                                [120*mb, 130*mb, 110*mb, 125*mb, 115*mb],
                                [5*mb, 6*mb, 4*mb, 5*mb, 5*mb])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'warning' in result['insights']
        assert '高压读取' in result['insights']['warning']

    def test_analyze_high_write_warning(self, analyzer):
        """TC-DA-04: 平均写>50MB/s 触发告警"""
        # Arrange
        mb = 1024 * 1024
        df = self._make_disk_df('nvme0',
                                [10*mb, 12*mb, 11*mb, 10*mb, 12*mb],
                                [60*mb, 65*mb, 55*mb, 70*mb, 50*mb])
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'warning' in result['insights']
        assert '高压写入' in result['insights']['warning']

    def test_analyze_multiple_disks(self, analyzer):
        """TC-DA-05: 多磁盘分组分析"""
        # Arrange - 两个磁盘
        mb = 1024 * 1024
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        df = pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(6)],
            'metric_type': ['disk'] * 6,
            'name': ['disk_read_bytes_per_sec'] * 6,
            'value': [10*mb, 12*mb, 11*mb, 20*mb, 22*mb, 21*mb],
            'labels': ['{"disk": "sda"}'] * 3 + ['{"disk": "sdb"}'] * 3,
            'labels_parsed': [{'disk': 'sda'}] * 3 + [{'disk': 'sdb'}] * 3,
        })
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert 'sda' in result['metrics']['disks']
        assert 'sdb' in result['metrics']['disks']

    def test_analyze_io_spike_detection(self, analyzer):
        """TC-DA-06: IQR 异常突刺检测"""
        # Arrange - 正常读取 + 一个极端突刺
        mb = 1024 * 1024
        df = self._make_disk_df('sda',
                                [10*mb] * 20 + [500*mb],
                                [5*mb] * 21)
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert - 异常检测应该被调用
        disk_stats = result['metrics']['disks']['sda']
        assert 'anomalies' in disk_stats['read']

    def test_analyze_no_disk_data(self, analyzer):
        """TC-DA-07: metric_type 无 disk 数据"""
        # Arrange - 有 metric_type 列但没有 disk 数据
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        df = pd.DataFrame({
            'timestamp': [base_time],
            'metric_type': ['cpu'],
            'name': ['cpu_usage_percent'],
            'value': [50.0],
            'labels': [{}],
            'labels_parsed': [{}],
        })
        
        # Act
        result = analyzer.analyze(df)
        
        # Assert
        assert result['insights'].get('summary') == '未采集到磁盘数据'
