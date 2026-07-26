"""
工具函数单元测试 (P0)
"""
import pytest
import pandas as pd
import numpy as np
from utils import parse_labels, extract_disk_name


class TestParseLabels:
    """parse_labels 函数测试"""

    def test_parse_labels_with_dict(self):
        """TC-UT-01: 输入已是 dict，直接返回"""
        # Arrange
        labels_dict = {'disk': 'sda', 'mount': '/'}
        
        # Act
        result = parse_labels(labels_dict)
        
        # Assert
        assert result == labels_dict
        assert result['disk'] == 'sda'

    def test_parse_labels_with_json_string(self):
        """TC-UT-02: JSON 字符串正确解析"""
        # Arrange
        labels_json = '{"disk": "sda", "mount": "/"}'
        
        # Act
        result = parse_labels(labels_json)
        
        # Assert
        assert isinstance(result, dict)
        assert result['disk'] == 'sda'
        assert result['mount'] == '/'

    def test_parse_labels_with_nan(self):
        """TC-UT-03: NaN 输入返回空 dict"""
        # Arrange
        labels_nan = np.nan
        
        # Act
        result = parse_labels(labels_nan)
        
        # Assert
        assert result == {}

    def test_parse_labels_with_invalid_string(self):
        """TC-UT-04: 非法字符串返回空 dict"""
        # Arrange
        invalid_string = 'not a valid json'
        
        # Act
        result = parse_labels(invalid_string)
        
        # Assert
        assert result == {}

    @pytest.mark.parametrize("input_value,expected", [
        ('{"disk": "sda"}', {'disk': 'sda'}),
        ('{"disk_name": "nvme0"}', {'disk_name': 'nvme0'}),
        ('{}', {}),
        ('{"key": "value"}', {'key': 'value'}),
    ])
    def test_parse_labels_various_inputs(self, input_value, expected):
        """参数化测试: 各种输入格式"""
        # Act
        result = parse_labels(input_value)
        
        # Assert
        assert result == expected


class TestExtractDiskName:
    """extract_disk_name 函数测试"""

    @pytest.mark.parametrize("labels_dict,expected", [
        ({'disk': 'sda'}, 'sda'),
        ({'disk': 'nvme0n1'}, 'nvme0n1'),
        ({'disk_name': 'sdb'}, 'sdb'),
    ])
    def test_extract_disk_name_with_valid_keys(self, labels_dict, expected):
        """TC-UT-05/06: 从 labels 提取 disk 名称"""
        # Act
        result = extract_disk_name(labels_dict)
        
        # Assert
        assert result == expected

    def test_extract_disk_name_missing_keys(self):
        """TC-UT-07: 无相关 key 返回 'unknown'"""
        # Arrange
        labels = {'mount': '/', 'type': 'ext4'}
        
        # Act
        result = extract_disk_name(labels)
        
        # Assert
        assert result == 'unknown'

    def test_extract_disk_name_non_dict(self):
        """TC-UT-08: 非 dict 输入返回 'unknown'"""
        # Arrange & Act & Assert
        assert extract_disk_name(None) == 'unknown'
        assert extract_disk_name('string') == 'unknown'
        assert extract_disk_name(123) == 'unknown'
        assert extract_disk_name([]) == 'unknown'

    def test_extract_disk_name_empty_values(self):
        """边界情况: disk key 存在但值为空"""
        # Arrange
        labels = {'disk': '', 'disk_name': None}
        
        # Act
        result = extract_disk_name(labels)
        
        # Assert - 空字符串和 None 都应该返回 'unknown'
        assert result == 'unknown'
