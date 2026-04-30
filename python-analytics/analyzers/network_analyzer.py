import logging
from typing import Dict, Any
import pandas as pd
from .base_analyzer import BaseMetricAnalyzer

logger = logging.getLogger(__name__)


class NetworkAnalyzer(BaseMetricAnalyzer):
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        result = {'metrics': {}, 'insights': {}}
        
        for name in ['network_received_bytes', 'network_transmitted_bytes']:
            net_df = df[df['name'] == name]
            if not net_df.empty:
                result['metrics'][name] = {
                    'stats': self.calculate_basic_stats(net_df['value']),
                    'trend': self.calculate_trend(net_df['value'])
                }
        return result
