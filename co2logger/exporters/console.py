"""
コンソール出力エクスポーター
"""
import logging
from typing import Union, List
from .base import DataExporterBase
from ..models.sensor_data import SensorDataBase

logger = logging.getLogger(__name__)


class ConsoleExporter(DataExporterBase):
    """コンソールにデータを出力するエクスポーター"""
    
    def __init__(self, verbose: bool = False):
        """
        コンソールエクスポーターを初期化
        
        Args:
            verbose: 詳細モードフラグ
        """
        self.verbose = verbose
    
    def set_verbose(self, verbose: bool):
        """
        詳細モードを設定
        
        Args:
            verbose: 詳細モードフラグ
        """
        self.verbose = verbose
    
    def format_data(self, data: SensorDataBase) -> str:
        """
        センサーデータをフォーマットして文字列化
        
        Args:
            data: センサーデータ
            
        Returns:
            フォーマットされた文字列
        """
        timestamp_str = data.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # CO2センサーデータの場合の特別な処理
        if hasattr(data, 'co2_ppm'):
            formatted = (
                f"[{timestamp_str}] "
                f"CO2: {data.co2_ppm} ppm, "
                f"Temp: {data.temperature}°C, "
                f"Humidity: {data.humidity}%, "
                f"Device: {data.device_address}"
            )
        else:
            # 基本的なセンサーデータのフォーマット
            formatted = f"[{timestamp_str}] Device: {data.device_address}"
        
        # 詳細モードの場合は生データも表示
        if self.verbose and hasattr(data, 'raw_data') and data.raw_data:
            formatted += f", Raw data: {data.raw_data}"
        
        return formatted
    
    async def export(self, data: Union[SensorDataBase, List[SensorDataBase]]) -> bool:
        """
        センサーデータをコンソールに出力
        
        Args:
            data: エクスポートするセンサーデータ（単一またはリスト）
            
        Returns:
            常にTrue（コンソール出力は基本的に失敗しない）
        """
        try:
            # データをリストに正規化
            if isinstance(data, list):
                data_list = data
            else:
                data_list = [data]
            
            # 各データを出力
            for sensor_data in data_list:
                formatted_output = self.format_data(sensor_data)
                print(formatted_output)
                logger.debug(f"コンソール出力: {formatted_output}")
            
            return True
            
        except Exception as e:
            logger.error(f"コンソール出力エラー: {e}")
            return False