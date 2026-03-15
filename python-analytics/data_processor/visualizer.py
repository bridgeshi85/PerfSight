"""
数据可视化模块
"""

import logging
from typing import Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px

from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class DataVisualizer:
    """数据可视化器"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.viz_config = config.visualization
        
        # 设置样式
        plt.style.use(self.viz_config.style)
        sns.set_palette(self.viz_config.color_palette)
    
    async def create_charts(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """创建所有图表"""
        charts = {}
        
        if df.empty:
            return charts
        
        logger.info("开始生成图表...")
        
        # 时间序列图表
        if 'timestamp' in df.columns:
            charts['time_series'] = await self._create_time_series_chart(df)
        
        # CPU 使用率图表
        cpu_data = df[df['metric_type'] == 'cpu_usage']
        if not cpu_data.empty:
            charts['cpu_usage'] = await self._create_cpu_chart(cpu_data)
        
        # 内存使用率图表
        memory_data = df[df['metric_type'] == 'memory_usage']
        if not memory_data.empty:
            charts['memory_usage'] = await self._create_memory_chart(memory_data)
        
        # 相关性热力图
        if 'correlations' in analysis_results and analysis_results['correlations']:
            charts['correlation_heatmap'] = await self._create_correlation_heatmap(df)
        
        logger.info(f"图表生成完成，共 {len(charts)} 个图表")
        return charts
    
    async def _create_time_series_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """创建时间序列图表"""
        fig, ax = plt.subplots(figsize=self.viz_config.figure_size)
        
        # 按指标类型分组绘制
        for metric_type in df['metric_type'].unique():
            metric_data = df[df['metric_type'] == metric_type]
            if 'value_parsed' in metric_data.columns:
                values = pd.to_numeric(metric_data['value_parsed'], errors='coerce')
            else:
                values = pd.to_numeric(metric_data['value'], errors='coerce')
            
            ax.plot(metric_data['timestamp'], values, label=metric_type, alpha=0.7)
        
        ax.set_xlabel('时间')
        ax.set_ylabel('值')
        ax.set_title('性能指标时间序列')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'type': 'time_series',
            'description': '性能指标随时间变化趋势'
        }
    
    async def _create_cpu_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """创建 CPU 使用率图表"""
        fig, ax = plt.subplots(figsize=self.viz_config.figure_size)
        
        if 'value_parsed' in df.columns:
            cpu_values = pd.to_numeric(df['value_parsed'], errors='coerce').dropna()
        else:
            cpu_values = pd.to_numeric(df['value'], errors='coerce').dropna()
        
        # 绘制 CPU 使用率分布
        ax.hist(cpu_values, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax.axvline(cpu_values.mean(), color='red', linestyle='--', label=f'平均值: {cpu_values.mean():.1f}%')
        ax.axvline(80, color='orange', linestyle='--', label='高使用率阈值: 80%')
        
        ax.set_xlabel('CPU 使用率 (%)')
        ax.set_ylabel('频次')
        ax.set_title('CPU 使用率分布')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'type': 'cpu_distribution',
            'description': 'CPU 使用率分布直方图'
        }
    
    async def _create_memory_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """创建内存使用率图表"""
        fig, ax = plt.subplots(figsize=self.viz_config.figure_size)
        
        # 简化的内存图表
        ax.text(0.5, 0.5, '内存使用率图表\n(待实现)', 
                ha='center', va='center', transform=ax.transAxes, fontsize=16)
        ax.set_title('内存使用率')
        
        return {
            'figure': fig,
            'type': 'memory_usage',
            'description': '内存使用率图表'
        }
    
    async def _create_correlation_heatmap(self, df: pd.DataFrame) -> Dict[str, Any]:
        """创建相关性热力图"""
        fig, ax = plt.subplots(figsize=self.viz_config.figure_size)
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
        else:
            ax.text(0.5, 0.5, '数据不足以生成相关性热力图', 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.set_title('指标相关性热力图')
        plt.tight_layout()
        
        return {
            'figure': fig,
            'type': 'correlation_heatmap',
            'description': '指标间相关性热力图'
        }