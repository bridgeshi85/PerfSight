"""
共享测试 fixtures
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_numeric_series():
    """正常数值序列"""
    return pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])


@pytest.fixture
def sample_series_with_outliers():
    """包含异常值的序列"""
    # 基础数据 + 两个极端异常值
    data = [10.0, 12.0, 11.0, 13.0, 12.0, 100.0, 5.0]
    return pd.Series(data)


@pytest.fixture
def sample_empty_series():
    """空序列"""
    return pd.Series([], dtype=float)


@pytest.fixture
def sample_series_with_nan():
    """包含 NaN 的序列"""
    return pd.Series([10.0, np.nan, 20.0, np.nan, 30.0])


@pytest.fixture
def sample_increasing_series():
    """上升趋势序列"""
    return pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])


@pytest.fixture
def sample_decreasing_series():
    """下降趋势序列"""
    return pd.Series([50.0, 40.0, 30.0, 20.0, 10.0])


@pytest.fixture
def sample_cpu_dataframe():
    """CPU 指标测试数据"""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    data = {
        'timestamp': [base_time + timedelta(minutes=i) for i in range(10)],
        'metric_type': ['cpu'] * 10,
        'name': ['cpu_usage_percent'] * 10,
        'value': [45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0],
        'labels': [{}] * 10
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_memory_dataframe():
    """内存指标测试数据"""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    data = {
        'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
        'metric_type': ['memory'] * 5,
        'name': ['memory_used_percent'] * 5,
        'value': [60.0, 65.0, 70.0, 75.0, 80.0],
        'value_parsed': [60.0, 65.0, 70.0, 75.0, 80.0],
        'labels': [{}] * 5
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_network_dataframe():
    """网络指标测试数据"""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    data = {
        'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
        'metric_type': ['network'] * 10,
        'name': ['network_received_bytes'] * 5 + ['network_transmitted_bytes'] * 5,
        'value': [1024*1024, 2*1024*1024, 3*1024*1024, 4*1024*1024, 5*1024*1024,
                  512*1024, 1024*1024, 1536*1024, 2048*1024, 2560*1024],
        'labels': [{}] * 10
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_disk_dataframe():
    """磁盘指标测试数据"""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    data = {
        'timestamp': [base_time + timedelta(minutes=i) for i in range(6)],
        'metric_type': ['disk'] * 6,
        'name': ['disk_read_bytes_per_sec'] * 3 + ['disk_write_bytes_per_sec'] * 3,
        'value': [10*1024*1024, 20*1024*1024, 15*1024*1024,  # 读: 10, 20, 15 MB/s
                  5*1024*1024, 8*1024*1024, 6*1024*1024],    # 写: 5, 8, 6 MB/s
        'labels': ['{"disk": "sda"}'] * 6,
        'labels_parsed': [{'disk': 'sda'}] * 6
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_clean_dataframe():
    """清洗后的标准测试数据"""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    data = {
        'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
        'metric_type': ['cpu', 'cpu', 'memory', 'memory', 'disk'],
        'name': ['cpu_usage_percent', 'load_average_1min', 
                 'memory_used_percent', 'memory_used_bytes',
                 'disk_read_bytes_per_sec'],
        'value': [50.0, 2.5, 70.0, 8*1024**3, 10*1024*1024],
        'value_parsed': [50.0, 2.5, 70.0, 8*1024**3, 10*1024*1024],
        'labels': [{}] * 4 + ['{"disk": "sda"}'],
        'labels_parsed': [{}] * 4 + [{'disk': 'sda'}]
    }
    return pd.DataFrame(data)
