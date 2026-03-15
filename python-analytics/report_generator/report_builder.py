"""
报告生成模块
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import base64
import io

from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class ReportBuilder:
    """报告构建器"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.report_config = config.report
    
    async def generate_html_report(self, df: pd.DataFrame, analysis_results: Dict[str, Any],
                                 charts: Dict[str, Any], ai_insights: Optional[Dict[str, Any]],
                                 output_dir: Path) -> Path:
        """生成 HTML 报告"""
        
        logger.info("生成 HTML 报告...")
        
        # 生成报告内容
        html_content = await self._build_html_content(df, analysis_results, charts, ai_insights)
        
        # 生成文件名
        timestamp = datetime.now().strftime(self.report_config.timestamp_format)
        filename = f"{self.report_config.filename_template.format(timestamp=timestamp)}.html"
        output_path = output_dir / filename
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML 报告已生成: {output_path}")
        return output_path
    
    async def generate_pdf_report(self, df: pd.DataFrame, analysis_results: Dict[str, Any],
                                charts: Dict[str, Any], ai_insights: Optional[Dict[str, Any]],
                                output_dir: Path) -> Path:
        """生成 PDF 报告"""
        
        logger.info("生成 PDF 报告...")
        
        # 先生成 HTML 内容
        html_content = await self._build_html_content(df, analysis_results, charts, ai_insights)
        
        # 生成文件名
        timestamp = datetime.now().strftime(self.report_config.timestamp_format)
        filename = f"{self.report_config.filename_template.format(timestamp=timestamp)}.pdf"
        output_path = output_dir / filename
        
        try:
            # 使用 weasyprint 转换为 PDF
            import weasyprint
            weasyprint.HTML(string=html_content).write_pdf(str(output_path))
            
        except ImportError:
            logger.warning("weasyprint 未安装，使用简化的 PDF 生成")
            # 创建一个简单的文本文件作为替代
            text_content = self._html_to_text(html_content)
            with open(output_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                f.write(text_content)
            output_path = output_path.with_suffix('.txt')
        
        except Exception as e:
            logger.error(f"PDF 生成失败: {e}")
            # 降级为文本文件
            text_content = self._html_to_text(html_content)
            with open(output_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                f.write(text_content)
            output_path = output_path.with_suffix('.txt')
        
        logger.info(f"PDF 报告已生成: {output_path}")
        return output_path
    
    async def _build_html_content(self, df: pd.DataFrame, analysis_results: Dict[str, Any],
                                charts: Dict[str, Any], ai_insights: Optional[Dict[str, Any]]) -> str:
        """构建 HTML 报告内容"""
        
        # 基础 HTML 模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PerfSight 性能分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }}
        .header .subtitle {{
            color: #666;
            margin-top: 10px;
            font-size: 1.1em;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-left: 4px solid #007bff;
            padding-left: 15px;
            margin-bottom: 20px;
        }}
        .section h3 {{
            color: #555;
            margin-bottom: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .stat-card h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .stat-card .value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #007bff;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .ai-insight {{
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
            margin: 20px 0;
        }}
        .ai-insight h4 {{
            color: #1976d2;
            margin: 0 0 10px 0;
        }}
        .suggestions {{
            background: #f1f8e9;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4caf50;
        }}
        .suggestions ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .suggestions li {{
            margin-bottom: 8px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 PerfSight 性能分析报告</h1>
            <div class="subtitle">生成时间: {timestamp}</div>
        </div>

        {content}

        <div class="footer">
            <p>📊 由 PerfSight Analytics Engine 生成 | 🤖 AI 驱动的智能分析</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 构建报告内容
        content_sections = []
        
        # 1. 数据概览
        content_sections.append(await self._build_overview_section(df, analysis_results))
        
        # 2. 性能指标分析
        content_sections.append(await self._build_metrics_section(analysis_results))
        
        # 3. 图表展示
        if self.report_config.include_charts and charts:
            content_sections.append(await self._build_charts_section(charts))
        
        # 4. AI 智能分析
        if self.report_config.include_ai_analysis and ai_insights:
            content_sections.append(await self._build_ai_section(ai_insights))
        
        # 5. 优化建议
        if self.report_config.include_recommendations and ai_insights:
            content_sections.append(await self._build_recommendations_section(ai_insights))
        
        # 6. 原始数据（可选）
        if self.report_config.include_raw_data:
            content_sections.append(await self._build_raw_data_section(df))
        
        content = '\n'.join(content_sections)
        
        return html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            content=content
        )
    
    async def _build_overview_section(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> str:
        """构建概览部分"""
        
        summary = analysis_results.get('summary', {})
        
        return f"""
        <div class="section">
            <h2>📊 数据概览</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>总记录数</h4>
                    <div class="value">{summary.get('total_records', 0):,}</div>
                </div>
                <div class="stat-card">
                    <h4>监控时长</h4>
                    <div class="value">{summary.get('time_range', {}).get('duration_hours', 0):.1f} 小时</div>
                </div>
                <div class="stat-card">
                    <h4>指标类型</h4>
                    <div class="value">{len(summary.get('metric_types', {}))}</div>
                </div>
                <div class="stat-card">
                    <h4>异常数量</h4>
                    <div class="value">{analysis_results.get('anomalies', {}).get('total_anomalies', 0)}</div>
                </div>
            </div>
        </div>
        """
    
    async def _build_metrics_section(self, analysis_results: Dict[str, Any]) -> str:
        """构建指标分析部分"""
        
        perf_metrics = analysis_results.get('performance_metrics', {})
        
        content = '<div class="section"><h2>⚡ 性能指标分析</h2>'
        
        # CPU 分析
        if 'cpu' in perf_metrics:
            cpu = perf_metrics['cpu']
            content += f"""
            <h3>🖥️ CPU 使用率</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>平均使用率</h4>
                    <div class="value">{cpu.get('avg_usage', 0):.1f}%</div>
                </div>
                <div class="stat-card">
                    <h4>最高使用率</h4>
                    <div class="value">{cpu.get('max_usage', 0):.1f}%</div>
                </div>
                <div class="stat-card">
                    <h4>高负载占比</h4>
                    <div class="value">{cpu.get('high_usage_percentage', 0):.1f}%</div>
                </div>
            </div>
            """
        
        content += '</div>'
        return content
    
    async def _build_charts_section(self, charts: Dict[str, Any]) -> str:
        """构建图表部分"""
        
        content = '<div class="section"><h2>📈 数据可视化</h2>'
        
        for chart_name, chart_data in charts.items():
            # 将图表转换为 base64 编码
            img_base64 = self._figure_to_base64(chart_data['figure'])
            
            content += f"""
            <div class="chart-container">
                <h3>{chart_data.get('description', chart_name)}</h3>
                <img src="data:image/png;base64,{img_base64}" alt="{chart_name}">
            </div>
            """
        
        content += '</div>'
        return content
    
    async def _build_ai_section(self, ai_insights: Dict[str, Any]) -> str:
        """构建 AI 分析部分"""
        
        content = '<div class="section"><h2>🧠 AI 智能分析</h2>'
        
        # 分析摘要
        if 'summary' in ai_insights:
            content += f"""
            <div class="ai-insight">
                <h4>📋 分析摘要</h4>
                <p>{ai_insights['summary']}</p>
            </div>
            """
        
        # 异常分析
        if 'anomaly_analysis' in ai_insights and ai_insights['anomaly_analysis']:
            content += f"""
            <div class="ai-insight">
                <h4>🔍 异常分析</h4>
                <p>{ai_insights['anomaly_analysis']}</p>
            </div>
            """
        
        # 根因分析
        if 'root_cause_analysis' in ai_insights and ai_insights['root_cause_analysis']:
            content += f"""
            <div class="ai-insight">
                <h4>🎯 根因分析</h4>
                <p>{ai_insights['root_cause_analysis']}</p>
            </div>
            """
        
        content += '</div>'
        return content
    
    async def _build_recommendations_section(self, ai_insights: Dict[str, Any]) -> str:
        """构建建议部分"""
        
        content = '<div class="section"><h2>💡 优化建议</h2>'
        
        if 'optimization_suggestions' in ai_insights:
            suggestions = ai_insights['optimization_suggestions']
            if suggestions:
                content += '<div class="suggestions"><h4>🚀 优化建议</h4><ul>'
                for suggestion in suggestions:
                    content += f'<li>{suggestion}</li>'
                content += '</ul></div>'
        
        content += '</div>'
        return content
    
    async def _build_raw_data_section(self, df: pd.DataFrame) -> str:
        """构建原始数据部分"""
        
        # 只显示前100行数据
        sample_df = df.head(100)
        
        content = f"""
        <div class="section">
            <h2>📄 原始数据样本</h2>
            <p>显示前 {len(sample_df)} 条记录（共 {len(df)} 条）</p>
            {sample_df.to_html(classes='table', table_id='raw-data-table')}
        </div>
        """
        
        return content
    
    def _figure_to_base64(self, figure) -> str:
        """将 matplotlib 图表转换为 base64 编码"""
        
        try:
            buffer = io.BytesIO()
            figure.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            return img_base64
        except Exception as e:
            logger.error(f"图表转换失败: {e}")
            return ""
    
    def _html_to_text(self, html_content: str) -> str:
        """将 HTML 转换为纯文本（简化版）"""
        
        # 简单的 HTML 标签移除
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()