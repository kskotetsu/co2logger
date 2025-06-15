"""
データエクスポーター基底クラス
"""
from abc import ABC, abstractmethod
from typing import Union, List
from ..models.sensor_data import SensorDataBase


class DataExporterBase(ABC):
    """データエクスポーターの抽象基底クラス"""
    
    @abstractmethod
    async def export(self, data: Union[SensorDataBase, List[SensorDataBase]]) -> bool:
        """
        センサーデータをエクスポートする
        
        Args:
            data: エクスポートするセンサーデータ（単一またはリスト）
            
        Returns:
            エクスポートが成功した場合True、失敗した場合False
        """
        pass