import pandas as pd
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DiskAnalyzer:
    """💽 磁盘 I/O 智能分析器 (适配时序性能数据)"""

    def __init__(self, config=None):
        self.config = config

    @staticmethod
    def analyze(df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析磁盘 I/O 数据流
        :param df: 包含全量监控数据的 Pandas DataFrame
        """
        if df is None or df.empty:
            return {}

        # 1. 过滤出磁盘数据
        disk_df = df[df['metric_type'] == 'disk'].copy()
        if disk_df.empty:
            return {"summary": "未采集到磁盘数据"}

        # 确保 value 是数值类型
        disk_df['value'] = pd.to_numeric(disk_df['value'], errors='coerce')
        disk_df = disk_df.dropna(subset=['value'])

        # 2. 解析 labels 获取具体磁盘名称 (应对 '{"disk":"Macintosh HD"}')
        def extract_disk_name(label_str):
            try:
                # 兼容不同格式的引号或 None
                if pd.isna(label_str): return 'unknown'
                labels = json.loads(label_str)
                return labels.get('disk') or labels.get('disk_name', 'unknown')
            except:
                return 'unknown'

        disk_df['disk_name'] = disk_df['labels'].apply(extract_disk_name)

        analysis_result = {
            "disks": {},
            "summary": "正常"
        }

        high_io_warnings = []

        # 3. 按磁盘名称分组进行统计算法分析
        for disk_name, group in disk_df.groupby('disk_name'):
            disk_stats = {}

            # --- 读取速率分析 ---
            read_df = group[group['name'] == 'disk_read_bytes_per_sec']
            if not read_df.empty:
                # 转换为 MB/s 以方便人类阅读
                read_mbps = read_df['value'] / (1024 * 1024)
                disk_stats['read'] = {
                    "avg_mbps": round(read_mbps.mean(), 2),
                    "max_mbps": round(read_mbps.max(), 2),
                    # 突刺算法：当前值如果大于平均值的 3 倍，且绝对值大于 10MB/s，则记为一次突刺
                    "spike_count": int(((read_mbps > read_mbps.mean() * 3) & (read_mbps > 10)).sum())
                }
            else:
                disk_stats['read'] = {"avg_mbps": 0.0, "max_mbps": 0.0, "spike_count": 0}

            # --- 写入速率分析 ---
            write_df = group[group['name'] == 'disk_write_bytes_per_sec']
            if not write_df.empty:
                write_mbps = write_df['value'] / (1024 * 1024)
                disk_stats['write'] = {
                    "avg_mbps": round(write_mbps.mean(), 2),
                    "max_mbps": round(write_mbps.max(), 2),
                    "spike_count": int(((write_mbps > write_mbps.mean() * 3) & (write_mbps > 10)).sum())
                }
            else:
                disk_stats['write'] = {"avg_mbps": 0.0, "max_mbps": 0.0, "spike_count": 0}

            analysis_result["disks"][disk_name] = disk_stats

            # 4. 生成诊断结论
            # 假设持续写入超过 50MB/s 或读取超过 100MB/s 属于高压状态 (阈值可根据你的 SSD 性能调整)
            if disk_stats['write']['avg_mbps'] > 50:
                high_io_warnings.append(f"[{disk_name}] 处于高压写入状态 (平均 {disk_stats['write']['avg_mbps']} MB/s)")
            if disk_stats['read']['avg_mbps'] > 100:
                high_io_warnings.append(f"[{disk_name}] 处于高压读取状态 (平均 {disk_stats['read']['avg_mbps']} MB/s)")
            if disk_stats['write']['spike_count'] > 5:
                high_io_warnings.append(
                    f"[{disk_name}] 出现频繁的写入毛刺 (共 {disk_stats['write']['spike_count']} 次突发落盘)")

        if high_io_warnings:
            analysis_result["summary"] = " | ".join(high_io_warnings)
        else:
            analysis_result["summary"] = "磁盘 I/O 运行平稳，未见明显读写瓶颈。"

        return analysis_result