"""
数据清洗模块
负责清洗和预处理从 Rust Agent 收集的性能数据
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
        
        # 查找所有数据文件
        json_files = list(data_path.glob("*.json"))
        csv_files = list(data_path.glob("*.csv"))
        
        all_data = []
        
        # 处理 JSON 文件
        for json_file in json_files:
            try:
                data = await self._load_json_file(json_file)
                if data:
                    all_data.extend(data)
                    logger.info(f"已加载 JSON 文件: {json_file.name}, {len(data)} 条记录")
            except Exception as e:
                logger.warning(f"加载 JSON 文件失败 {json_file.name}: {e}")
        
        # 处理 CSV 文件
        for csv_file in csv_files:
            try:
                data = await self._load_csv_file(csv_file)
                if not data.empty:
                    # 将 DataFrame 转换为字典列表
                    records = data.to_dict('records')
                    all_data.extend(records)
                    logger.info(f"已加载 CSV 文件: {csv_file.name}, {len(records)} 条记录")
            except Exception as e:
                logger.warning(f"加载 CSV 文件失败 {csv_file.name}: {e}")
        
        if not all_data:
            logger.warning("未找到有效数据")
            return pd.DataFrame()
        
        # 转换为 DataFrame 并清洗
        df = pd.DataFrame(all_data)
        return await self._clean_dataframe(df)
    
    async def clean_file(self, file_path: str) -> pd.DataFrame:
        """清洗单个数据文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if file_path.suffix.lower() == '.json':
            data = await self._load_json_file(file_path)
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)
        elif file_path.suffix.lower() == '.csv':
            df = await self._load_csv_file(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")
        
        return await self._clean_dataframe(df)
    
    async def _load_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """加载 JSON 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果是单个对象，转换为列表
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"JSON 文件格式不正确: {file_path}")
                return []
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误 {file_path}: {e}")
            return []

    async def _load_csv_file(self, file_path: Path) -> pd.DataFrame:
        """加载 CSV 文件"""
        try:
            # 尝试不同的编码
            for encoding in ['utf-8', 'gbk', 'latin-1']:
                try:
                    # 🚀 核心修复：添加 on_bad_lines='skip'
                    # 当 Pandas 遇到列数被 JSON 逗号撑爆的异常行时，直接静默跳过，绝不崩溃！
                    # (注意：如果你的 Pandas 版本低于 1.3.0，请把 on_bad_lines='skip' 换成 error_bad_lines=False)
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        on_bad_lines='skip',
                        engine='c'  # 保持 C 引擎以获得最高性能
                    )
                    return df
                except UnicodeDecodeError:
                    continue

            # 如果走到这里，使用兜底方案
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                errors='ignore',
                on_bad_lines='skip'
            )
            return df

        except Exception as e:
            # 这里的 logger 异常捕获非常正确
            logger.error(f"CSV 加载错误 {file_path}: {e}")
            return pd.DataFrame()
    
    async def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗 DataFrame"""
        if df.empty:
            return df
        
        logger.info(f"开始清洗数据，原始记录数: {len(df)}")
        
        # 1. 标准化时间戳列
        df = self._normalize_timestamp(df)
        
        # 2. 移除重复记录
        if self.dp_config.remove_duplicates:
            df = self._remove_duplicates(df)
        
        # 3. 处理缺失值
        if self.dp_config.fill_missing_values:
            df = self._fill_missing_values(df)
        
        # 4. 异常值检测和处理
        if self.dp_config.outlier_detection:
            df = self._handle_outliers(df)
        
        # 5. 数据类型转换
        df = self._convert_data_types(df)
        
        # 6. 过滤无效数据
        df = self._filter_invalid_data(df)
        
        # 7. 时间序列重采样（如果配置了）
        if self.dp_config.resample_interval:
            df = self._resample_time_series(df)
        
        logger.info(f"数据清洗完成，最终记录数: {len(df)}")
        
        return df
    
    def _normalize_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化时间戳列"""
        time_col = self.dp_config.time_column
        
        if time_col not in df.columns:
            # 尝试查找可能的时间列
            time_candidates = ['timestamp', 'time', 'datetime', 'created_at']
            for candidate in time_candidates:
                if candidate in df.columns:
                    time_col = candidate
                    break
            else:
                logger.warning("未找到时间戳列，使用当前时间")
                df[self.dp_config.time_column] = pd.Timestamp.now()
                return df
        
        try:
            # 转换时间戳
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            
            # 移除无效时间戳的行
            invalid_time_mask = df[time_col].isna()
            if invalid_time_mask.any():
                logger.warning(f"移除 {invalid_time_mask.sum()} 条无效时间戳记录")
                df = df[~invalid_time_mask]
            
            # 确保时间戳列名一致
            if time_col != self.dp_config.time_column:
                df = df.rename(columns={time_col: self.dp_config.time_column})
            
            # 按时间排序
            df = df.sort_values(self.dp_config.time_column)
            
        except Exception as e:
            logger.error(f"时间戳标准化失败: {e}")
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """移除重复记录"""
        original_count = len(df)
        
        # 基于时间戳和主要指标列去重
        subset_cols = [self.dp_config.time_column]
        
        # 添加主要的标识列
        for col in ['name', 'metric_type', 'labels']:
            if col in df.columns:
                subset_cols.append(col)
        
        df = df.drop_duplicates(subset=subset_cols, keep='last')
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            logger.info(f"移除重复记录: {removed_count} 条")
        
        return df
    
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """填充缺失值"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if df[col].isna().any():
                # 对于数值列，使用前向填充，然后用均值填充
                df[col] = df[col].fillna(method='ffill').fillna(df[col].mean())
        
        # 对于字符串列，使用 "unknown" 填充
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            if col != self.dp_config.time_column:  # 不处理时间戳列
                df[col] = df[col].fillna('unknown')
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理异常值"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        threshold = self.dp_config.outlier_threshold
        
        for col in numeric_columns:
            if col in df.columns and df[col].std() > 0:
                # 使用 Z-score 方法检测异常值
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outlier_mask = z_scores > threshold
                
                if outlier_mask.any():
                    outlier_count = outlier_mask.sum()
                    logger.info(f"检测到 {col} 列的异常值: {outlier_count} 个")
                    
                    # 用中位数替换异常值
                    median_value = df[col].median()
                    df.loc[outlier_mask, col] = median_value
        
        return df
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换数据类型"""
        # 尝试将 value 列转换为数值类型
        if 'value' in df.columns:
            # 如果 value 是 JSON 字符串，尝试解析
            if df['value'].dtype == 'object':
                try:
                    # 尝试解析 JSON
                    df['value_parsed'] = df['value'].apply(self._parse_value)
                except Exception as e:
                    logger.warning(f"解析 value 列失败: {e}")
        
        # 转换标签列
        if 'labels' in df.columns and df['labels'].dtype == 'object':
            try:
                df['labels_parsed'] = df['labels'].apply(self._parse_labels)
            except Exception as e:
                logger.warning(f"解析 labels 列失败: {e}")
        
        return df
    
    def _parse_value(self, value) -> Any:
        """解析 value 字段"""
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            try:
                # 尝试解析为 JSON
                parsed = json.loads(value)
                return parsed
            except json.JSONDecodeError:
                # 尝试转换为数值
                try:
                    return float(value)
                except ValueError:
                    return value
        
        return value
    
    def _parse_labels(self, labels) -> Dict[str, str]:
        """解析 labels 字段"""
        if pd.isna(labels):
            return {}
        
        if isinstance(labels, dict):
            return labels
        
        if isinstance(labels, str):
            try:
                return json.loads(labels)
            except json.JSONDecodeError:
                return {}
        
        return {}
    
    def _filter_invalid_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤无效数据"""
        original_count = len(df)
        
        # 移除数据点过少的情况
        if len(df) < self.dp_config.min_data_points:
            logger.warning(f"数据点过少 ({len(df)} < {self.dp_config.min_data_points})，跳过处理")
            return pd.DataFrame()
        
        # 检查时间间隔
        if self.dp_config.time_column in df.columns:
            time_diffs = df[self.dp_config.time_column].diff()
            max_gap = timedelta(minutes=self.dp_config.max_gap_minutes)
            
            large_gaps = time_diffs > max_gap
            if large_gaps.any():
                logger.info(f"检测到 {large_gaps.sum()} 个大时间间隔")
        
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            logger.info(f"过滤无效数据: {filtered_count} 条")
        
        return df
    
    def _resample_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """重采样时间序列"""
        if self.dp_config.time_column not in df.columns:
            return df
        
        try:
            # 设置时间戳为索引
            df_resampled = df.set_index(self.dp_config.time_column)
            
            # 重采样
            interval = self.dp_config.resample_interval
            df_resampled = df_resampled.resample(interval).mean()
            
            # 重置索引
            df_resampled = df_resampled.reset_index()
            
            logger.info(f"时间序列重采样完成，间隔: {interval}")
            
            return df_resampled
        
        except Exception as e:
            logger.error(f"时间序列重采样失败: {e}")
            return df