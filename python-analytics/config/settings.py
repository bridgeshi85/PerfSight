import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DataProcessingConfig:
    """数据处理配置"""
    time_column: str = "timestamp"
    outlier_threshold: float = 3.0  # Z-score 阈值，用于剔除毛刺


@dataclass
class VisualizationConfig:
    enable_cpu_chart: bool = True
    enable_memory_chart: bool = True
    enable_network_chart: bool = True
    enable_disk_chart: bool = True
    figure_size: tuple = (12, 6)
    output_dir: str = "./reports/charts"


@dataclass
class AnalyticsConfig:
    """主配置类"""
    data_processing: DataProcessingConfig = field(default_factory=DataProcessingConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)

    debug: bool = False

    @classmethod
    def load_from_file(cls, config_path: str) -> 'AnalyticsConfig':
        """从文件加载配置，使用优雅的解包方式"""
        config_file = Path(config_path)

        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path}，将使用默认配置。")
            return cls()

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        return cls(
            data_processing=DataProcessingConfig(**data.get('data_processing', {})),
            visualization=VisualizationConfig(**data.get('visualization', {})),
            debug=data.get('debug', False)
        )

    def save_to_file(self, config_path: str):
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(self), f, default_flow_style=False, allow_unicode=True, indent=2)