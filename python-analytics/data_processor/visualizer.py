"""
数据可视化模块 (现代化 Plotly 重构版)
"""

import logging
from typing import Dict, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class DataVisualizer:
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.viz_config = config.visualization

        # 统一的图表样式配置
        self.layout_template = "plotly_white"
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

    async def create_charts(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """总控流水线：根据配置和数据，创建所有交互式图表"""
        charts = {}
        if df.empty:
            return charts

        logger.info("开始生成现代化 Plotly 交互式图表...")

        val_col = 'value_parsed' if 'value_parsed' in df.columns else 'value'

        # 1. 绘制 CPU 相关图表
        if self.viz_config.enable_cpu_chart:
            cpu_charts = await self._create_cpu_dashboards(df, val_col)
            charts.update(cpu_charts)

        # 2. 绘制 Memory 相关图表
        if self.viz_config.enable_memory_chart:
            mem_charts = await self._create_memory_dashboards(df, val_col)
            charts.update(mem_charts)

        # 3. 绘制 Network 相关图表 (如果你后续在配置里打开了)
        if getattr(self.viz_config, 'enable_network_chart', True):
            net_charts = await self._create_network_dashboards(df, val_col)
            charts.update(net_charts)

        # 4. 绘制 Disk I/O 相关图表
        if getattr(self.viz_config, 'enable_disk_chart', True):
            disk_charts = await self._create_disk_dashboards(df, val_col)
            charts.update(disk_charts)

        logger.info(f"图表生成完成，共 {len(charts)} 个可视化面板")
        return charts

    async def _create_cpu_dashboards(self, df: pd.DataFrame, val_col: str) -> Dict[str, Any]:
        """创建 CPU 监控仪表盘 (仅保留时间趋势折线图)"""
        cpu_df = df[df['metric_type'] == 'cpu'].copy()
        if cpu_df.empty: return {}

        cpu_df[val_col] = pd.to_numeric(cpu_df[val_col], errors='coerce')
        cpu_df = cpu_df.dropna(subset=[val_col])

        # 仅保留 CPU 使用率时间趋势图
        fig = go.Figure()

        cpu_percent_df = cpu_df[cpu_df['name'] == 'cpu_usage_percent']

        if not cpu_percent_df.empty:
            # 将带有 +00:00 时区的时间转为标准字符串，防止 JSON 序列化崩溃
            x_data = cpu_percent_df['timestamp'].astype(str).tolist()
            y_data = cpu_percent_df[val_col].tolist()
            mean_val = float(cpu_percent_df[val_col].mean())

            # 趋势折线图
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines+markers',  # 🚀 加上 markers，画出折线的同时标出具体的采样圆点
                    name='CPU Usage (%)',
                    line=dict(color=self.colors[0], width=2),
                    marker=dict(size=6)
                )
            )

            # 添加阈值参考线
            fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80% 警戒")
            fig.add_hline(y=mean_val, line_dash="dot", line_color="green", annotation_text=f"平均: {mean_val:.1f}%")

        # 样式美化
        fig.update_layout(
            title_text="🚀 CPU 性能监控面板",
            template=self.layout_template,
            height=500,
            showlegend=True,
            hovermode="x unified"
        )

        # 🚀 强制声明 X 轴为真实时间轴 (Date Type)，确保时间间隔的物理比例正确
        fig.update_xaxes(type="date", title_text="真实时间")

        # 🚀 强制锁定 CPU 的 Y 轴为 0~100%，防止 Plotly 自适应缩放导致微小波动看起来像大地震
        fig.update_yaxes(title_text="百分比 (%)", range=[0, 100])

        return {'cpu_dashboard': {'figure': fig, 'type': 'plotly_html'}}

    async def _create_memory_dashboards(self, df: pd.DataFrame, val_col: str) -> Dict[str, Any]:
        """创建 Memory 监控仪表盘 (双 Y 轴折线图)"""
        mem_df = df[df['metric_type'] == 'memory'].copy()
        if mem_df.empty:
            return {}

        mem_df[val_col] = pd.to_numeric(mem_df[val_col], errors='coerce')
        mem_df = mem_df.dropna(subset=[val_col])

        # 创建带有辅助 Y 轴的图表
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # 1. 主 Y 轴画百分比 (used_percent)
        percent_df = mem_df[mem_df['name'] == 'memory_used_percent']
        if not percent_df.empty:
            x_data = percent_df['timestamp'].astype(str).tolist()
            y_data = percent_df[val_col].tolist()
            avg_percent = float(percent_df[val_col].mean())
            fig.add_trace(
                go.Scatter(x=x_data, y=y_data,
                           mode='lines+markers', name='使用率 (%)', fill='tozeroy',
                           line=dict(color=self.colors[1], width=2),
                           marker=dict(size=6)),
                secondary_y=False,
            )

            # 在主 Y 轴上标注平均使用率，便于快速观察整体水平
            fig.add_hline(
                y=avg_percent,
                line_dash="dot",
                line_color="green",
                annotation_text=f"平均使用率: {avg_percent:.1f}%",
                secondary_y=False,
            )

        # Y轴绝对值字节数 (used_bytes)
        bytes_df = mem_df[mem_df['name'] == 'memory_used_bytes']
        if not bytes_df.empty:
            x_data_bytes = bytes_df['timestamp'].astype(str).tolist()
            y_data_gb = [round(y / (1024 ** 3), 2) for y in bytes_df[val_col].tolist()]

            fig.add_trace(
                go.Scatter(x=x_data_bytes, y=y_data_gb,
                           mode='lines+markers', name='使用量 (GB)',  # 🚀 名字改成 GB
                           line=dict(color=self.colors[2], width=2, dash='dot'),
                           marker=dict(size=6)),
                secondary_y=True,
            )

        # 样式美化
        fig.update_layout(
            title_text="🧠 内存资源监控面板",
            template=self.layout_template,
            height=500,
            hovermode="x unified"
        )
        fig.update_xaxes(type="date", title_text="真实时间")
        fig.update_yaxes(title_text="内存使用率 (%)", range=[0, 100], secondary_y=False)
        fig.update_yaxes(title_text="内存量 (GB)", secondary_y=True)

        return {'memory_dashboard': {'figure': fig, 'type': 'plotly_html'}}

    async def _create_network_dashboards(self, df: pd.DataFrame, val_col: str) -> Dict[str, Any]:
        """创建 Network 网络监控仪表盘"""
        net_df = df[df['metric_type'] == 'network'].copy()
        if net_df.empty: return {}

        net_df[val_col] = pd.to_numeric(net_df[val_col], errors='coerce')
        net_df = net_df.dropna(subset=[val_col])

        fig = go.Figure()

        rx_df = net_df[net_df['name'] == 'network_received_bytes']
        if not rx_df.empty:
            x_data_rx = rx_df['timestamp'].astype(str).tolist()
            y_data_rx_mb = [round(y / (1024 ** 2), 3) for y in rx_df[val_col].tolist()]
            fig.add_trace(
                go.Scatter(
                    x=x_data_rx,
                    y=y_data_rx_mb,
                    mode='lines+markers',
                    name='⬇️ 接收 (MB)',
                    line=dict(color=self.colors[2], width=2),
                    marker=dict(size=6)
                )
            )

        tx_df = net_df[net_df['name'] == 'network_transmitted_bytes']
        if not tx_df.empty:
            x_data_tx = tx_df['timestamp'].astype(str).tolist()
            y_data_tx_mb = [round(y / (1024 ** 2), 3) for y in tx_df[val_col].tolist()]
            fig.add_trace(
                go.Scatter(
                    x=x_data_tx,
                    y=y_data_tx_mb,
                    mode='lines+markers',
                    name='⬆️ 发送 (MB)',
                    line=dict(color=self.colors[3], width=2),
                    marker=dict(size=6)
                )
            )

        fig.update_layout(
            title_text="🌐 网络吞吐量监控",
            template=self.layout_template,
            height=400,
            yaxis_title="吞吐量 (MB)",
            hovermode="x unified"
        )
        fig.update_xaxes(type="date", title_text="真实时间")

        return {'network_dashboard': {'figure': fig, 'type': 'plotly_html'}}

    async def _create_disk_dashboards(self, df: pd.DataFrame, val_col: str) -> Dict[str, Any]:
        """创建 Disk I/O 监控仪表盘 (专属性能测试视角)"""
        disk_df = df[df['metric_type'] == 'disk'].copy()
        if disk_df.empty: return {}

        disk_df[val_col] = pd.to_numeric(disk_df[val_col], errors='coerce')
        disk_df = disk_df.dropna(subset=[val_col])

        if 'labels_parsed' in disk_df.columns:
            disk_df['disk_name'] = disk_df['labels_parsed'].apply(
                lambda x: (x.get('disk') or x.get('disk_name') or 'unknown') if isinstance(x, dict) else 'unknown')
        else:
            disk_df['disk_name'] = 'Total'

        fig = go.Figure()

        unique_disks = disk_df['disk_name'].unique()

        for disk_name in unique_disks:
            specific_disk_df = disk_df[disk_df['disk_name'] == disk_name]

            # 1. 读速率 (MB/s)
            read_df = specific_disk_df[specific_disk_df['name'] == 'disk_read_bytes_per_sec']
            if not read_df.empty:
                x_data = read_df['timestamp'].astype(str).tolist()
                # 🚀 转换为 MB/s 更符合直觉
                y_data_mb = [round(y / (1024 ** 2), 2) for y in read_df[val_col].tolist()]

                fig.add_trace(
                    go.Scatter(x=x_data, y=y_data_mb,
                               mode='lines+markers', name=f'{disk_name} ⬇️ 读取 (MB/s)',
                               line=dict(color=self.colors[2], width=2),
                               marker=dict(size=6))
                )

            # 2. 写速率 (MB/s)
            write_df = specific_disk_df[specific_disk_df['name'] == 'disk_write_bytes_per_sec']
            if not write_df.empty:
                x_data = write_df['timestamp'].astype(str).tolist()
                y_data_mb = [round(y / (1024 ** 2), 2) for y in write_df[val_col].tolist()]

                fig.add_trace(
                    go.Scatter(x=x_data, y=y_data_mb,
                               mode='lines+markers', name=f'{disk_name} ⬆️ 写入 (MB/s)',
                               line=dict(color=self.colors[3], width=2, dash='dot'),
                               marker=dict(size=6))
                )

        # 样式美化
        fig.update_layout(
            title_text="💽 磁盘 I/O 吞吐量监控面板 (性能视角)",
            template=self.layout_template,
            height=400,
            hovermode="x unified",
            yaxis_title="吞吐速率 (MB/s)"
        )

        fig.update_xaxes(type="date", title_text="真实时间")

        return {'disk_io_dashboard': {'figure': fig, 'type': 'plotly_html'}}
