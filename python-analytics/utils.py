"""
项目级共享工具函数
"""

import json
from typing import Any, Dict

import pandas as pd


def parse_labels(raw_labels: Any) -> Dict[str, Any]:
    """将 labels 字段（可能是 dict / JSON 字符串 / NaN）统一解析为 dict"""
    if isinstance(raw_labels, dict):
        return raw_labels
    if pd.isna(raw_labels):
        return {}
    try:
        return json.loads(raw_labels)
    except (ValueError, TypeError, json.JSONDecodeError):
        return {}


def extract_disk_name(labels: Any) -> str:
    """从解析后的 labels dict 中提取磁盘名称，取不到则返回 'unknown'"""
    if not isinstance(labels, dict):
        return 'unknown'
    return labels.get('disk') or labels.get('disk_name') or 'unknown'
