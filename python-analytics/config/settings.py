"""
PerfSight Analytics 配置管理
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class DataProcessingConfig:
    """数据处理配置"""
    # 数据清洗配置
    remove_duplicates: bool = True
    fill_missing_values: bool = True
    outlier_detection: bool = True
    outlier_threshold: float = 3.0  # Z-score 阈值
    
    # 时间序列配置
    time_column: str = "timestamp"
    resample_interval: Optional[str] = None  # 如 "1min", "5min"
    
    # 数据过滤配置
    min_data_points: int = 10
    max_gap_minutes: int = 60


@dataclass
class VisualizationConfig:
    """可视化配置"""
    # 图表样式
    style: str = "seaborn-v0_8"
    color_palette: str = "husl"
    figure_size: tuple = (12, 8)
    dpi: int = 300
    
    # 图表类型配置
    enable_interactive: bool = True
    save_static: bool = True
    
    # 图表内容配置
    show_trends: bool = True
    show_anomalies: bool = True
    show_correlations: bool = True


@dataclass
class AIAnalysisConfig:
    """AI 分析配置"""
    # LLM 提供商配置
    provider: str = "openai"  # openai, anthropic, local
    
    # OpenAI 配置
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model: str = "gpt-4"
    openai_base_url: Optional[str] = None
    
    # Anthropic 配置
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    anthropic_model: str = "claude-3-sonnet-20240229"
    
    # 本地模型配置
    local_model_url: Optional[str] = None
    local_model_name: str = "llama2"
    
    # 分析配置
    enable_anomaly_detection: bool = True
    enable_root_cause_analysis: bool = True
    enable_optimization_suggestions: bool = True
    
    # 请求配置
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout_seconds: int = 60


@dataclass
class ReportConfig:
    """报告生成配置"""
    # 报告模板
    html_template: str = "default.html"
    pdf_template: str = "default.html"
    
    # 报告内容
    include_raw_data: bool = False
    include_charts: bool = True
    include_ai_analysis: bool = True
    include_recommendations: bool = True
    
    # 报告格式
    html_theme: str = "bootstrap"
    pdf_page_size: str = "A4"
    pdf_orientation: str = "portrait"
    
    # 文件命名
    filename_template: str = "perfsight_report_{timestamp}"
    timestamp_format: str = "%Y%m%d_%H%M%S"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # PostgreSQL 配置
    postgres_enabled: bool = False
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "perfsight"
    postgres_username: str = "postgres"
    postgres_password: Optional[str] = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD"))
    
    # Redis 配置
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_database: int = 0
    redis_password: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))


@dataclass
class AnalyticsConfig:
    """主配置类"""
    # 子配置
    data_processing: DataProcessingConfig = field(default_factory=DataProcessingConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    ai_analysis: AIAnalysisConfig = field(default_factory=AIAnalysisConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # 全局配置
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 4
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'AnalyticsConfig':
        """从文件加载配置"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {config_file.suffix}")
        
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsConfig':
        """从字典创建配置对象"""
        config = cls()
        
        # 更新数据处理配置
        if 'data_processing' in data:
            dp_data = data['data_processing']
            config.data_processing = DataProcessingConfig(**dp_data)
        
        # 更新可视化配置
        if 'visualization' in data:
            viz_data = data['visualization']
            config.visualization = VisualizationConfig(**viz_data)
        
        # 更新 AI 分析配置
        if 'ai_analysis' in data:
            ai_data = data['ai_analysis']
            config.ai_analysis = AIAnalysisConfig(**ai_data)
        
        # 更新报告配置
        if 'report' in data:
            report_data = data['report']
            config.report = ReportConfig(**report_data)
        
        # 更新数据库配置
        if 'database' in data:
            db_data = data['database']
            config.database = DatabaseConfig(**db_data)
        
        # 更新全局配置
        for key in ['debug', 'log_level', 'max_workers', 'cache_enabled', 'cache_ttl_seconds']:
            if key in data:
                setattr(config, key, data[key])
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data_processing': {
                'remove_duplicates': self.data_processing.remove_duplicates,
                'fill_missing_values': self.data_processing.fill_missing_values,
                'outlier_detection': self.data_processing.outlier_detection,
                'outlier_threshold': self.data_processing.outlier_threshold,
                'time_column': self.data_processing.time_column,
                'resample_interval': self.data_processing.resample_interval,
                'min_data_points': self.data_processing.min_data_points,
                'max_gap_minutes': self.data_processing.max_gap_minutes,
            },
            'visualization': {
                'style': self.visualization.style,
                'color_palette': self.visualization.color_palette,
                'figure_size': self.visualization.figure_size,
                'dpi': self.visualization.dpi,
                'enable_interactive': self.visualization.enable_interactive,
                'save_static': self.visualization.save_static,
                'show_trends': self.visualization.show_trends,
                'show_anomalies': self.visualization.show_anomalies,
                'show_correlations': self.visualization.show_correlations,
            },
            'ai_analysis': {
                'provider': self.ai_analysis.provider,
                'openai_model': self.ai_analysis.openai_model,
                'anthropic_model': self.ai_analysis.anthropic_model,
                'local_model_name': self.ai_analysis.local_model_name,
                'enable_anomaly_detection': self.ai_analysis.enable_anomaly_detection,
                'enable_root_cause_analysis': self.ai_analysis.enable_root_cause_analysis,
                'enable_optimization_suggestions': self.ai_analysis.enable_optimization_suggestions,
                'max_tokens': self.ai_analysis.max_tokens,
                'temperature': self.ai_analysis.temperature,
                'timeout_seconds': self.ai_analysis.timeout_seconds,
            },
            'report': {
                'html_template': self.report.html_template,
                'pdf_template': self.report.pdf_template,
                'include_raw_data': self.report.include_raw_data,
                'include_charts': self.report.include_charts,
                'include_ai_analysis': self.report.include_ai_analysis,
                'include_recommendations': self.report.include_recommendations,
                'html_theme': self.report.html_theme,
                'pdf_page_size': self.report.pdf_page_size,
                'pdf_orientation': self.report.pdf_orientation,
                'filename_template': self.report.filename_template,
                'timestamp_format': self.report.timestamp_format,
            },
            'database': {
                'postgres_enabled': self.database.postgres_enabled,
                'postgres_host': self.database.postgres_host,
                'postgres_port': self.database.postgres_port,
                'postgres_database': self.database.postgres_database,
                'postgres_username': self.database.postgres_username,
                'redis_enabled': self.database.redis_enabled,
                'redis_host': self.database.redis_host,
                'redis_port': self.database.redis_port,
                'redis_database': self.database.redis_database,
            },
            'debug': self.debug,
            'log_level': self.log_level,
            'max_workers': self.max_workers,
            'cache_enabled': self.cache_enabled,
            'cache_ttl_seconds': self.cache_ttl_seconds,
        }
    
    def save_to_file(self, config_path: str):
        """保存配置到文件"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, 
                     allow_unicode=True, indent=2)
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        # 验证 AI 配置
        if self.ai_analysis.provider == "openai" and not self.ai_analysis.openai_api_key:
            errors.append("OpenAI API Key 未设置")
        
        if self.ai_analysis.provider == "anthropic" and not self.ai_analysis.anthropic_api_key:
            errors.append("Anthropic API Key 未设置")
        
        # 验证数据库配置
        if self.database.postgres_enabled and not self.database.postgres_password:
            errors.append("PostgreSQL 密码未设置")
        
        if self.database.redis_enabled and not self.database.redis_password:
            errors.append("Redis 密码未设置")
        
        return errors