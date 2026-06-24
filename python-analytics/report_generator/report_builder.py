import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import pandas as pd

from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class ReportBuilder:
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        # 动态定位模板文件路径 (假设 templates 文件夹在项目根目录)
        self.template_path = Path(__file__).resolve().parent.parent / "templates" / "report_template.html"

    async def generate_html_report(self, analysis_results: Dict[str, Any],
                                   charts: Dict[str, Any],
                                   output_dir: Path) -> Path:
        logger.info("开始装配交互式 HTML 报告...")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. 检查模板是否存在
        if not self.template_path.exists():
            logger.error(f"找不到报告模板文件: {self.template_path}")
            raise FileNotFoundError(f"Missing template: {self.template_path}")

        # 2. 读取模板内容
        with open(self.template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()

        # 3. 渲染各个组件
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        overview_cards = self._build_overview_cards(analysis_results)
        charts_html = self._build_plotly_charts(charts)

        # 4. 组装最终 HTML
        final_html = html_template.format(
            timestamp=timestamp,
            overview_cards=overview_cards,
            charts_html=charts_html,
        )

        # 5. 生成文件名并保存
        file_name = f"perfsight_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = output_dir / file_name

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)

        logger.info(f"✅ HTML 交互式报告已生成: {output_path}")
        return output_path

    @staticmethod
    def _build_overview_cards(analysis_results: Dict[str, Any]) -> str:
        """构建概览卡片 (适配最新的 MetricsProcessor 输出结构)"""
        summary = analysis_results.get('summary', {})
        total_records = summary.get('total_records', 0)

        # 计算时长
        time_range = summary.get('time_range', {})
        start_str = time_range.get('start')
        end_str = time_range.get('end')
        duration_mins = 0

        if start_str and end_str:
            start_dt = pd.to_datetime(start_str)
            end_dt = pd.to_datetime(end_str)
            duration_mins = (end_dt - start_dt).total_seconds() / 60

        cards_html = f"""
        <div class="stat-card">
            <h4>总采集数据点</h4>
            <div class="value">{total_records:,}</div>
        </div>
        <div class="stat-card">
            <h4>压测持续时长</h4>
            <div class="value">{duration_mins:.1f} 分钟</div>
        </div>
        """

        # 提取 CPU 报警信息 (从新架构中)
        cpu_metrics = analysis_results.get('categories', {}).get('cpu', {}).get('metrics', {})
        cpu_usage = cpu_metrics.get('cpu_usage_percent', {})
        high_load_ratio = cpu_usage.get('high_load_ratio', 0)

        cards_html += f"""
        <div class="stat-card" style="border-top-color: {'#e74c3c' if high_load_ratio > 0 else '#2ecc71'};">
            <h4>CPU 超载时间占比</h4>
            <div class="value" style="color: {'#e74c3c' if high_load_ratio > 0 else '#2ecc71'};">{high_load_ratio:.1f}%</div>
        </div>
        """

        return cards_html

    @staticmethod
    def _build_plotly_charts(charts: Dict[str, Any]) -> str:
        """将 Plotly Figure 对象转换为纯净的 HTML Div 字符串"""
        if not charts:
            return "<p>未生成任何图表</p>"

        charts_html = ""
        for chart_name, chart_data in charts.items():
            fig = chart_data.get('figure')
            if fig:
                # 核心魔法：将 Plotly 转为无需外置依赖的 HTML div 代码片段
                div_html = fig.to_html(full_html=False, include_plotlyjs=False)
                charts_html += f"""
                <div class="chart-container">
                    {div_html}
                </div>
                """
        return charts_html

