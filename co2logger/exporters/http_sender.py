"""
HTTP送信エクスポーター
"""
import json
import logging
import asyncio
from typing import Union, List, Dict, Any, Optional
import aiohttp
from .base import DataExporterBase
from ..models.sensor_data import SensorDataBase

logger = logging.getLogger(__name__)


class HttpSender(DataExporterBase):
    """センサーデータをHTTPでサーバーに送信するエクスポーター"""
    
    def __init__(self, url: str, timeout: float = 10.0, max_retries: int = 3):
        """
        HTTP送信エクスポーターを初期化
        
        Args:
            url: 送信先のURL
            timeout: タイムアウト時間（秒）
            max_retries: 最大リトライ回数
        """
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "co2logger/1.0"
        }
    
    def set_authentication(self, auth_type: str, token: str):
        """
        認証情報を設定
        
        Args:
            auth_type: 認証タイプ（例: "Bearer", "Basic"）
            token: 認証トークン
        """
        self.headers["Authorization"] = f"{auth_type} {token}"
    
    def add_headers(self, custom_headers: Dict[str, str]):
        """
        カスタムヘッダーを追加
        
        Args:
            custom_headers: 追加するヘッダーの辞書
        """
        self.headers.update(custom_headers)
    
    def _convert_to_dict(self, data: SensorDataBase) -> Dict[str, Any]:
        """
        センサーデータを辞書形式に変換
        
        Args:
            data: センサーデータ
            
        Returns:
            辞書形式のデータ
        """
        return data.to_dict()
    
    async def _send_data(self, payload: Dict[str, Any]) -> bool:
        """
        データをHTTPで送信
        
        Args:
            payload: 送信するペイロード
            
        Returns:
            送信が成功した場合True、失敗した場合False
        """
        for attempt in range(self.max_retries + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        self.url,
                        data=json.dumps(payload),
                        headers=self.headers
                    ) as response:
                        if response.status == 200:
                            logger.info(f"データ送信成功: {self.url}")
                            return True
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"HTTP送信失敗 (試行{attempt + 1}/{self.max_retries + 1}): "
                                f"ステータス={response.status}, レスポンス={error_text}"
                            )
                            
                            if attempt < self.max_retries:
                                # リトライ前に待機（指数バックオフ）
                                wait_time = (2 ** attempt) * 1.0
                                await asyncio.sleep(wait_time)
                            
            except Exception as e:
                logger.error(
                    f"HTTP送信エラー (試行{attempt + 1}/{self.max_retries + 1}): {e}"
                )
                
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0
                    await asyncio.sleep(wait_time)
        
        logger.error(f"最大リトライ回数を超えました: {self.url}")
        return False
    
    async def export(self, data: Union[SensorDataBase, List[SensorDataBase]]) -> bool:
        """
        センサーデータをHTTPで送信
        
        Args:
            data: エクスポートするセンサーデータ（単一またはリスト）
            
        Returns:
            送信が成功した場合True、失敗した場合False
        """
        try:
            # データをリストに正規化
            if isinstance(data, list):
                data_list = [self._convert_to_dict(item) for item in data]
            else:
                data_list = self._convert_to_dict(data)
            
            # ペイロードを作成
            if isinstance(data, list):
                # 複数データの場合は配列として送信
                payload = data_list
            else:
                # 単一データの場合はオブジェクトとして送信
                payload = data_list
            
            # HTTP送信を実行
            return await self._send_data(payload)
            
        except Exception as e:
            logger.error(f"データエクスポートエラー: {e}")
            return False