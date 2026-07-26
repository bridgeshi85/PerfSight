"""
数据清洗器单元测试 (P1)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from data_processor.cleaner import DataCleaner
from config.settings import AnalyticsConfig, DataProcessingConfig


class TestDataCleanerFileOperations:
    """文件操作相关测试"""

    def test_clean_directory_not_found(self, tmp_path):
        """TC-CL-01: 目录不存在抛 FileNotFoundError"""
        # Arrange
        config = AnalyticsConfig()
        cleaner = DataCleaner(config)
        non_existent_dir = tmp_path / 'non_existent'
        
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="数据目录不存在"):
            cleaner.clean_directory(str(non_existent_dir))

    def test_clean_directory_empty(self, tmp_path):
        """TC-CL-02: 空目录返回空 DataFrame"""
        # Arrange
        config = AnalyticsConfig()
        cleaner = DataCleaner(config)
        empty_dir = tmp_path / 'empty_data'
        empty_dir.mkdir()
        
        # Act
        result = cleaner.clean_directory(str(empty_dir))
        
        # Assert
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_clean_file_valid_csv(self, tmp_path):
        """TC-CL-03: 正常 CSV 清洗成功"""
        # Arrange - 创建测试 CSV
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        csv_content = "timestamp,metric_type,name,value,labels\n"
        for i in range(5):
            timestamp = (base_time + timedelta(minutes=i)).isoformat()
            csv_content += f"{timestamp},cpu,cpu_usage_percent,{50.0 + i},{{}}\n"
        
        csv_file = tmp_path / 'test_data.csv'
        csv_file.write_text(csv_content)
        
        config = AnalyticsConfig()
        cleaner = DataCleaner(config)
        
        # Act
        result = cleaner.clean_file(str(csv_file))
        
        # Assert
        assert not result.empty
        assert 'timestamp' in result.columns
        assert 'value_parsed' in result.columns
        assert len(result) == 5

    def test_clean_file_not_found(self, tmp_path):
        """TC-CL-10: 文件不存在抛异常"""
        # Arrange
        config = AnalyticsConfig()
        cleaner = DataCleaner(config)
        non_existent_file = tmp_path / 'non_existent.csv'
        
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            cleaner.clean_file(str(non_existent_file))


class TestDataCleanerPipeline:
    """数据清洗管道测试"""

    @pytest.fixture
    def cleaner(self):
        """提供 DataCleaner 实例"""
        config = AnalyticsConfig()
        return DataCleaner(config)

    def test_normalize_timestamp(self, cleaner):
        """TC-CL-04: 时间戳正确标准化并排序"""
        # Arrange - 乱序的时间戳
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        df = pd.DataFrame({
            'timestamp': [
                (base_time + timedelta(minutes=2)).isoformat(),
                (base_time + timedelta(minutes=0)).isoformat(),
                (base_time + timedelta(minutes=1)).isoformat(),
            ],
            'value': [30.0, 10.0, 20.0]
        })
        
        # Act
        result = cleaner._normalize_timestamp(df)
        
        # Assert - 应该按时间排序
        assert result['timestamp'].is_monotonic_increasing
        assert result.iloc[0]['value'] == 10.0  # 最早的时间

    def test_convert_values_numeric(self, cleaner):
        """TC-CL-05: 字符串值转浮点数"""
        # Arrange
        df = pd.DataFrame({
            'value': ['10.5', '20.3', '30.7']
        })
        
        # Act
        result = cleaner._convert_values(df)
        
        # Assert
        assert 'value_parsed' in result.columns
        assert result['value_parsed'].iloc[0] == 10.5
        assert result['value_parsed'].iloc[1] == 20.3

    def test_convert_values_drop_invalid(self, cleaner):
        """TC-CL-06: 无法转换的行被丢弃"""
        # Arrange - 包含无法转换的值
        df = pd.DataFrame({
            'value': ['10.5', 'invalid', '30.7', 'NaN']
        })
        
        # Act
        result = cleaner._convert_values(df)
        
        # Assert - 无效行被丢弃
        assert len(result) == 2  # 只有 '10.5' 和 '30.7' 有效
        assert result['value_parsed'].iloc[0] == 10.5
        assert result['value_parsed'].iloc[1] == 30.7

    def test_parse_labels_pipeline(self, cleaner):
        """TC-CL-07: labels JSON 正确解析为 dict"""
        # Arrange
        df = pd.DataFrame({
            'labels': ['{"disk": "sda"}', '{"disk": "sdb"}', '{}']
        })
        
        # Act
        result = cleaner._parse_labels(df)
        
        # Assert
        assert 'labels_parsed' in result.columns
        assert result['labels_parsed'].iloc[0] == {'disk': 'sda'}
        assert result['labels_parsed'].iloc[1] == {'disk': 'sdb'}
        assert result['labels_parsed'].iloc[2] == {}

    def test_handle_outliers_zscore(self, cleaner):
        """TC-CL-08: Z-score 异常值被中位数替换"""
        # Arrange - 需要足够多的正常值，让异常值在 Z-score 下显著
        # 30 个正常值 + 1 个极端值
        df = pd.DataFrame({
            'name': ['cpu'] * 31,
            'value_parsed': [50.0, 51.0, 49.0, 50.0, 52.0, 48.0, 50.0, 51.0, 49.0, 50.0,
                             50.0, 51.0, 49.0, 50.0, 52.0, 48.0, 50.0, 51.0, 49.0, 50.0,
                             50.0, 51.0, 49.0, 50.0, 52.0, 48.0, 50.0, 51.0, 49.0, 50.0,
                             500.0]
        })
        
        # Act
        result = cleaner._handle_outliers(df)
        
        # Assert - 极端值 500 应该被替换为中位数
        assert result['value_parsed'].max() < 100  # 500 被替换
        assert result['value_parsed'].min() > 40   # 所有值都在正常范围内

    def test_handle_outliers_disabled(self, cleaner):
        """TC-CL-09: threshold<=0 时不做处理"""
        # Arrange
        cleaner.dp_config.outlier_threshold = 0.0
        df = pd.DataFrame({
            'name': ['cpu'] * 5,
            'value_parsed': [50.0, 52.0, 51.0, 200.0, 5.0]
        })
        
        # Act
        result = cleaner._handle_outliers(df)
        
        # Assert - 数据保持不变
        assert result['value_parsed'].max() == 200.0
        assert result['value_parsed'].min() == 5.0


class TestDataCleanerIntegration:
    """集成测试: 完整清洗流程"""

    def test_clean_directory_with_valid_csv(self, tmp_path):
        """集成测试: 完整目录清洗流程"""
        # Arrange - 创建测试 CSV
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        csv_content = "timestamp,metric_type,name,value,labels\n"
        for i in range(10):
            timestamp = (base_time + timedelta(minutes=i)).isoformat()
            csv_content += f"{timestamp},cpu,cpu_usage_percent,{50.0 + i},{{}}\n"
        
        csv_file = tmp_path / 'test_data.csv'
        csv_file.write_text(csv_content)
        
        config = AnalyticsConfig()
        cleaner = DataCleaner(config)
        
        # Act
        result = cleaner.clean_directory(str(tmp_path))
        
        # Assert
        assert not result.empty
        assert len(result) == 10
        assert 'timestamp' in result.columns
        assert 'value_parsed' in result.columns
        assert 'labels_parsed' in result.columns
