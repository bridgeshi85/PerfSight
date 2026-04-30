"""
数据清洗模块
负责清洗和预处理从 Rust Agent 收集的扁平化性能数据
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗器"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.dp_config = config.data_processing

    async def clean_directory(self, data_dir: str) -> pd.DataFrame:
        """清洗目录中的所有数据文件"""
        data_path = Path(data_dir)

        if not data_path.exists():
            raise FileNotFoundError(f"数据目录不存在: {data_dir}")

        csv_files = list(data_path.glob("*.csv"))
        all_data = []

        # 目前 Rust 探针主要输出 CSV，我们专注处理 CSV
        for csv_file in csv_files:
            try:
                data = await self._load_csv_file(csv_file)
                if not data.empty:
                    all_data.extend(data.to_dict('records'))
                    logger.info(f"已加载 CSV 文件: {csv_file.name}, {len(data)} 条记录")
            except Exception as e:
                logger.warning(f"加载 CSV 文件失败 {csv_file.name}: {e}")

        if not all_data:
            logger.warning("未找到有效数据")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        return self._clean_dataframe(df)  # 移除了 async，因为内部全是同步的 Pandas 操作

    async def clean_file(self, file_path: str) -> pd.DataFrame:
        """清洗单个数据文件"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        df = await self._load_csv_file(file_path)
        return self._clean_dataframe(df)

    async def _load_csv_file(self, file_path: Path) -> pd.DataFrame:
        """加载 CSV 文件 (带容错机制)"""
        try:
            # 使用 on_bad_lines='skip' 完美防御极个别由于系统原因导致的断行错乱
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                on_bad_lines='skip',
                engine='c'
            )
            return df
        except Exception as e:
            logger.error(f"CSV 加载错误 {file_path}: {e}")
            return pd.DataFrame()

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗 DataFrame 核心流水线"""
        if df.empty:
            return df

        logger.info(f"开始清洗数据，原始记录数: {len(df)}")

        # 1. 标准化时间戳列
        df = self._normalize_timestamp(df)

        # 2. 转换数值类型 (核心！将字符串变成真正的浮点数)
        df = self._convert_values(df)

        # 3. 解析 Labels 标签 (如果后续需要按网卡/磁盘切分数据)
        df = self._parse_labels(df)

        # 4. 异常值处理 (Z-score 剔除操作系统偶发的非理性毛刺)
        df = self._handle_outliers(df)

        logger.info(f"数据清洗完成，最终有效记录数: {len(df)}")
        return df

    def _normalize_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化时间戳并排序"""
        time_col = self.dp_config.time_column

        if time_col not in df.columns:
            logger.warning(f"未找到配置的时间列 {time_col}，清洗中断")
            return df

        try:
            # 强制转换为 datetime 对象，无法转换的变为 NaT
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')

            # 剔除时间损坏的行，并按时间线严格排序
            df = df.dropna(subset=[time_col]).sort_values(time_col)
        except Exception as e:
            logger.error(f"时间戳标准化失败: {e}")

        return df

    def _convert_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """安全转换 Value 列为数值型"""
        if 'value' in df.columns:
            # 抛弃原来复杂的 JSON 嗅探，直接强制转浮点数 (Rust 已经发来纯净数字)
            df['value_parsed'] = pd.to_numeric(df['value'], errors='coerce')
            # 剔除转换失败(变成 NaN)的无效行
            df = df.dropna(subset=['value_parsed'])
        return df

    def _parse_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """将 JSON 格式的 labels 字符串转为真实的 Python 字典"""
        if 'labels' in df.columns:
            def safe_json_load(x):
                if isinstance(x, dict): return x
                try: return json.loads(x) if isinstance(x, str) else {}
                except: return {}

            df['labels_parsed'] = df['labels'].apply(safe_json_load)
        return df

    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理极端异常值 (Z-score 算法)"""
        threshold = self.dp_config.outlier_threshold
        if threshold <= 0 or 'value_parsed' not in df.columns:
            return df

        # 根据指标名称 (name) 分组处理异常值，因为 CPU 和 Memory 的量级完全不同
        for name, group in df.groupby('name'):
            s = group['value_parsed']
            if s.std() > 0:
                # 计算 Z-score
                z_scores = np.abs((s - s.mean()) / s.std())
                outlier_mask = z_scores > threshold

                if outlier_mask.any():
                    count = outlier_mask.sum()
                    logger.debug(f"[{name}] 压制了 {count} 个极端毛刺数据")
                    # 用中位数平滑替换掉毛刺
                    df.loc[outlier_mask.index[outlier_mask], 'value_parsed'] = s.median()

        return df