"""
JSONファイル出力エクスポーター
"""
import json
import logging
import os
from typing import Union, List, Dict, Any
from .base import DataExporterBase
from ..models.sensor_data import SensorDataBase

logger = logging.getLogger(__name__)


class JsonFileExporter(DataExporterBase):
    """センサーデータをJSONファイルに出力するエクスポーター"""
    
    def __init__(self, file_path: str, append_mode: bool = False):
        """
        JSONファイルエクスポーターを初期化
        
        Args:
            file_path: 出力ファイルのパス
            append_mode: 追記モード（Trueの場合は既存ファイルに追記）
        """
        self.file_path = file_path
        self.append_mode = append_mode
    
    def _load_existing_data(self) -> List[Dict[str, Any]]:
        """
        既存のJSONファイルからデータを読み込み
        
        Returns:
            既存データのリスト（ファイルが存在しない場合は空リスト）
        """
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"既存ファイルの読み込みに失敗: {e}")
            return []
    
    def _convert_to_dict(self, data: SensorDataBase) -> Dict[str, Any]:
        """
        センサーデータを辞書形式に変換
        
        Args:
            data: センサーデータ
            
        Returns:
            辞書形式のデータ
        """
        return data.to_dict()
    
    async def export(self, data: Union[SensorDataBase, List[SensorDataBase]]) -> bool:
        """
        センサーデータをJSONファイルに出力
        
        Args:
            data: エクスポートするセンサーデータ（単一またはリスト）
            
        Returns:
            エクスポートが成功した場合True、失敗した場合False
        """
        try:
            # データをリストに正規化
            if isinstance(data, list):
                new_data_list = [self._convert_to_dict(item) for item in data]
            else:
                new_data_list = [self._convert_to_dict(data)]
            
            # 追記モードの場合は既存データを読み込み
            if self.append_mode:
                existing_data = self._load_existing_data()
                all_data = existing_data + new_data_list
            else:
                all_data = new_data_list
            
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # JSONファイルに書き込み
            with open(self.file_path, 'w', encoding='utf-8') as file:
                json.dump(all_data, file, indent=2, ensure_ascii=False)
            
            logger.info(f"JSONファイルに{len(new_data_list)}件のデータを出力: {self.file_path}")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"JSONファイル出力エラー: {e}")
            raise  # テストで例外をキャッチできるように再発生
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            return False