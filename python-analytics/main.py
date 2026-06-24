#!/usr/bin/env python3
"""
PerfSight Analytics Engine
性能数据分析和智能诊断引擎
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from config.settings import AnalyticsConfig
from data_processor.cleaner import DataCleaner
from data_processor.visualizer import DataVisualizer
from report_generator.report_builder import ReportBuilder
from data_processor.metrics_processor import MetricsProcessor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("perfsight.analytics")
console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True),
              help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """PerfSight Analytics Engine - 性能数据分析和智能诊断"""

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 加载配置
    if config:
        ctx.obj = AnalyticsConfig.load_from_file(config)
    else:
        ctx.obj = AnalyticsConfig()

    console.print("🚀 [bold blue]PerfSight Analytics Engine[/bold blue]")
    console.print(f"📊 配置文件: {config or '默认配置'}")


@cli.command()
@click.option('--input-dir', '-i', type=click.Path(exists=True),
              required=True, help='输入数据目录')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./reports', help='输出报告目录')
@click.option('--format', '-f', type=click.Choice(['html', 'pdf', 'both']),
              default='html', help='报告格式')
@click.pass_obj
def analyze(config: AnalyticsConfig, input_dir: str, output_dir: str, format: str):
    """分析性能数据并生成报告"""

    asyncio.run(_analyze_async(config, input_dir, output_dir, format))


async def _analyze_async(config: AnalyticsConfig, input_dir: str,
                         output_dir: str, format: str):
    """异步分析函数"""

    try:
        console.print(f"📂 输入目录: {input_dir}")
        console.print(f"📁 输出目录: {output_dir}")

        # 1. 数据清洗
        console.print("\n🧹 [bold yellow]步骤 1: 数据清洗[/bold yellow]")
        cleaner = DataCleaner(config)
        cleaned_data = await cleaner.clean_directory(input_dir)

        if cleaned_data.empty:
            console.print("❌ [red]未找到有效数据[/red]")
            return

        console.print(f"✅ 清洗完成，共 {len(cleaned_data)} 条记录")

        # 2. 数据分析
        console.print("\n📊 [bold yellow]步骤 2: 数据分析[/bold yellow]")
        processor = MetricsProcessor(config)
        analysis_results = await processor.process(cleaned_data)

        console.print(f"✅ 分析完成 ")

        # 3. 数据可视化
        console.print("\n📈 [bold yellow]步骤 3: 数据可视化[/bold yellow]")
        visualizer = DataVisualizer(config)
        charts = await visualizer.create_charts(cleaned_data, analysis_results)

        console.print(f"✅ 可视化完成，生成 {len(charts)} 个图表")

        # 4. 生成报告
        console.print("\n📄 [bold yellow]步骤 4: 生成报告[/bold yellow]")
        report_builder = ReportBuilder(config)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        html_path = await report_builder.generate_html_report(
            analysis_results, charts, output_path
        )
        console.print(f"✅ HTML 报告: {html_path}")

        console.print("\n🎉 [bold green]分析完成！[/bold green]")

    except Exception as e:
        logger.error(f"分析过程中发生错误: {e}", exc_info=True)
        console.print(f"❌ [red]错误: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--input-file', '-i', type=click.Path(exists=True),
              required=True, help='输入数据文件')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./charts', help='图表输出目录')
@click.pass_obj
def visualize(config: AnalyticsConfig, input_file: str, output_dir: str):
    """仅生成数据可视化图表"""

    asyncio.run(_visualize_async(config, input_file, output_dir))


async def _visualize_async(config: AnalyticsConfig, input_file: str, output_dir: str):
    """异步可视化函数"""

    try:
        console.print(f"📂 输入文件: {input_file}")
        console.print(f"📁 输出目录: {output_dir}")

        # 数据清洗
        cleaner = DataCleaner(config)
        cleaned_data = await cleaner.clean_file(input_file)

        if cleaned_data.empty:
            console.print("❌ [red]未找到有效数据[/red]")
            return

        # 数据分析
        processor = MetricsProcessor(config)
        analysis_results = await processor.process(cleaned_data)

        # 生成图表
        visualizer = DataVisualizer(config)
        charts = await visualizer.create_charts(cleaned_data, analysis_results)

        # 保存图表
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for chart_name, chart_data in charts.items():
            chart_path = output_path / f"{chart_name}.png"
            chart_data['figure'].savefig(chart_path, dpi=300, bbox_inches='tight')
            console.print(f"✅ 图表已保存: {chart_path}")

        console.print(f"\n🎉 [bold green]可视化完成！共生成 {len(charts)} 个图表[/bold green]")

    except Exception as e:
        logger.error(f"可视化过程中发生错误: {e}", exc_info=True)
        console.print(f"❌ [red]错误: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(),
              default='./config.yaml', help='配置文件输出路径')
def init_config(output: str):
    """生成默认配置文件"""

    try:
        config = AnalyticsConfig()
        config.save_to_file(output)
        console.print(f"✅ [green]默认配置文件已生成: {output}[/green]")

    except Exception as e:
        console.print(f"❌ [red]生成配置文件失败: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()
