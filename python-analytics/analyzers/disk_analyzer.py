import logging
from typing import Dict, Any
import pandas as pd
from .base_analyzer import BaseMetricAnalyzer

logger = logging.getLogger(__name__)


class DiskAnalyzer(BaseMetricAnalyzer):
    """💽 磁盘 I/O 智能分析器 (适配时序性能数据)"""

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析磁盘 I/O 数据流
        :param df: 包含全量监控数据的 Pandas DataFrame
        """
        result = {'metrics': {}, 'insights': {}}

        if df is None or df.empty:
            return result

        # 1. 过滤出磁盘数据
        disk_df = df[df['metric_type'] == 'disk'].copy()
        if disk_df.empty:
            result['insights']['summary'] = '未采集到磁盘数据'
            return result

        # 确保 value 是数值类型
        disk_df['value'] = pd.to_numeric(disk_df['value'], errors='coerce')
        disk_df = disk_df.dropna(subset=['value'])

        # 2. 解析 labels 获取磁盘名称
        disk_df['labels_parsed'] = disk_df['labels'].apply(self._parse_labels)
        disk_df['disk_name'] = disk_df['labels_parsed'].apply(self._extract_disk_name)

        # 3. 按磁盘名称分组，复用基类统计工具进行分析
        result['metrics']['disks'] = {}
        high_io_warnings = []

        for disk_name, group in disk_df.groupby('disk_name'):
            disk_stats = {}

            # --- 读取速率分析 (转换为 MB/s) ---
            read_df = group[group['name'] == 'disk_read_bytes_per_sec']
            if not read_df.empty:
                read_mbps = read_df['value'] / (1024 * 1024)
                disk_stats['read'] = {
                    'stats': self.calculate_basic_stats(read_mbps),
                    'trend': self.calculate_trend(read_mbps),
                    'anomalies': self.detect_anomalies_iqr(read_mbps),
                }
            else:
                disk_stats['read'] = {'stats': {}, 'trend': {}, 'anomalies': {'count': 0}}

            # --- 写入速率分析 (转换为 MB/s) ---
            write_df = group[group['name'] == 'disk_write_bytes_per_sec']
            if not write_df.empty:
                write_mbps = write_df['value'] / (1024 * 1024)
                disk_stats['write'] = {
                    'stats': self.calculate_basic_stats(write_mbps),
                    'trend': self.calculate_trend(write_mbps),
                    'anomalies': self.detect_anomalies_iqr(write_mbps),
                }
            else:
                disk_stats['write'] = {'stats': {}, 'trend': {}, 'anomalies': {'count': 0}}

            result['metrics']['disks'][disk_name] = disk_stats

            # 4. 生成诊断结论 (与 CPU/Memory 对齐的阈值告警逻辑)
            read_stats = disk_stats['read'].get('stats', {})
            write_stats = disk_stats['write'].get('stats', {})
            read_anomalies = disk_stats['read'].get('anomalies', {})
            write_anomalies = disk_stats['write'].get('anomalies', {})

            # 高压告警：平均读 > 100MB/s 或平均写 > 50MB/s
            if read_stats.get('mean', 0) > 100:
                high_io_warnings.append(
                    f"[{disk_name}] 处于高压读取状态 (平均 {read_stats['mean']:.1f} MB/s)")
            if write_stats.get('mean', 0) > 50:
                high_io_warnings.append(
                    f"[{disk_name}] 处于高压写入状态 (平均 {write_stats['mean']:.1f} MB/s)")

            # IQR 异常检测告警：异常点占比 > 5%
            if read_anomalies.get('percentage', 0) > 5:
                high_io_warnings.append(
                    f"[{disk_name}] 读取存在 {read_anomalies['count']} 次 I/O 突刺 "
                    f"(占比 {read_anomalies['percentage']:.1f}%)")
            if write_anomalies.get('percentage', 0) > 5:
                high_io_warnings.append(
                    f"[{disk_name}] 写入存在 {write_anomalies['count']} 次 I/O 突刺 "
                    f"(占比 {write_anomalies['percentage']:.1f}%)")

            # 趋势告警：持续上升的 I/O 趋势
            read_trend = disk_stats['read'].get('trend', {})
            write_trend = disk_stats['write'].get('trend', {})
            if read_trend.get('direction') == 'increasing' and read_trend.get('r_squared', 0) > 0.7:
                high_io_warnings.append(f"[{disk_name}] 读取速率呈持续上升趋势")
            if write_trend.get('direction') == 'increasing' and write_trend.get('r_squared', 0) > 0.7:
                high_io_warnings.append(f"[{disk_name}] 写入速率呈持续上升趋势")

        if high_io_warnings:
            result['insights']['summary'] = ' | '.join(high_io_warnings)
            result['insights']['warning'] = result['insights']['summary']
        else:
            result['insights']['summary'] = '磁盘 I/O 运行平稳，未见明显读写瓶颈。'

        return result

    @staticmethod
    def _parse_labels(raw_labels):
        """兼容字符串 JSON / dict / 空值，统一生成 labels_parsed"""
        if isinstance(raw_labels, dict):
            return raw_labels
        if pd.isna(raw_labels):
            return {}
        try:
            import json
            return json.loads(raw_labels)
        except (ValueError, TypeError):
            return {}

    @staticmethod
    def _extract_disk_name(labels):
        """从解析后的 labels 中提取磁盘名称"""
        if not isinstance(labels, dict):
            return 'unknown'
        return labels.get('disk') or labels.get('disk_name', 'unknown')
