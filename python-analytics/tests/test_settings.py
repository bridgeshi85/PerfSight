"""
配置管理单元测试 (P1)
"""
import pytest
import yaml
from pathlib import Path
from config.settings import AnalyticsConfig, DataProcessingConfig, VisualizationConfig


class TestAnalyticsConfig:
    """AnalyticsConfig 类测试"""

    def test_default_config_values(self):
        """TC-CF-01: 默认配置值正确"""
        # Arrange & Act
        config = AnalyticsConfig()
        
        # Assert
        assert config.debug is False
        assert config.data_processing.time_column == 'timestamp'
        assert config.data_processing.outlier_threshold == 3.0
        assert config.visualization.enable_cpu_chart is True
        assert config.visualization.enable_memory_chart is True

    def test_load_from_file_valid_yaml(self, tmp_path):
        """TC-CF-02: 正常 YAML 文件加载"""
        # Arrange
        config_data = {
            'debug': True,
            'data_processing': {
                'time_column': 'time',
                'outlier_threshold': 2.5
            },
            'visualization': {
                'enable_cpu_chart': False,
                'figure_size': [10, 5]
            }
        }
        config_file = tmp_path / 'test_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Act
        config = AnalyticsConfig.load_from_file(str(config_file))
        
        # Assert
        assert config.debug is True
        assert config.data_processing.time_column == 'time'
        assert config.data_processing.outlier_threshold == 2.5
        assert config.visualization.enable_cpu_chart is False
        assert config.visualization.figure_size == [10, 5]

    def test_load_from_file_missing(self, tmp_path):
        """TC-CF-03: 文件不存在返回默认配置"""
        # Arrange
        non_existent_file = tmp_path / 'non_existent.yaml'
        
        # Act
        config = AnalyticsConfig.load_from_file(str(non_existent_file))
        
        # Assert - 应该返回默认配置
        assert config.debug is False
        assert config.data_processing.time_column == 'timestamp'

    def test_load_from_file_partial(self, tmp_path):
        """TC-CF-04: 部分配置覆盖，其余默认"""
        # Arrange - 只覆盖部分配置
        config_data = {
            'debug': True,
            'data_processing': {
                'outlier_threshold': 2.0
            }
        }
        config_file = tmp_path / 'partial_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Act
        config = AnalyticsConfig.load_from_file(str(config_file))
        
        # Assert - 覆盖的值和默认值
        assert config.debug is True
        assert config.data_processing.outlier_threshold == 2.0
        assert config.data_processing.time_column == 'timestamp'  # 默认值
        assert config.visualization.enable_cpu_chart is True  # 默认值

    def test_save_and_reload_roundtrip(self, tmp_path):
        """TC-CF-05: 保存后重新加载数据一致"""
        # Arrange
        original_config = AnalyticsConfig()
        original_config.debug = True
        original_config.data_processing.outlier_threshold = 2.5
        original_config.visualization.enable_cpu_chart = False
        
        config_file = tmp_path / 'roundtrip_config.yaml'
        
        # Act - 保存
        original_config.save_to_file(str(config_file))
        
        # Act - 重新加载
        loaded_config = AnalyticsConfig.load_from_file(str(config_file))
        
        # Assert
        assert loaded_config.debug == original_config.debug
        assert loaded_config.data_processing.outlier_threshold == original_config.data_processing.outlier_threshold
        assert loaded_config.visualization.enable_cpu_chart == original_config.visualization.enable_cpu_chart

    def test_data_processing_config_override(self):
        """TC-CF-06: 自定义 outlier_threshold"""
        # Arrange & Act
        config = DataProcessingConfig(outlier_threshold=2.0)
        
        # Assert
        assert config.outlier_threshold == 2.0
        assert config.time_column == 'timestamp'  # 默认值保持不变

    def test_visualization_config_defaults(self):
        """TC-CF-07: 可视化默认开关正确"""
        # Arrange & Act
        config = VisualizationConfig()
        
        # Assert
        assert config.enable_cpu_chart is True
        assert config.enable_memory_chart is True
        assert config.enable_network_chart is True
        assert config.enable_disk_chart is True
        assert config.figure_size == [12, 6]
        assert config.output_dir == './reports/charts'
