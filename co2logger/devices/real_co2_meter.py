#!/usr/bin/env python3
"""
実際のCO2計 (B0:E9:FE:58:74:AE, 製造者ID: 2409) 専用クラス
"""

import struct
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from ..models.sensor_data import CO2SensorData

logger = logging.getLogger(__name__)


class RealCO2Meter:
    """実際のCO2計専用クラス"""
    
    # 実際のCO2計の識別情報
    MANUFACTURER_ID = 2409
    SERVICE_UUID = "0000fd3d-0000-1000-8000-00805f9b34fb"
    
    def __init__(self, ble_device: BLEDevice):
        """
        CO2計を初期化
        
        Args:
            ble_device: BLEデバイスオブジェクト
        """
        self.device = ble_device
        self.device_address = ble_device.address
        self.device_name = ble_device.name or "Real CO2 Meter"
        self.latest_data: Optional[CO2SensorData] = None
        
    @classmethod
    def is_real_co2_meter(cls, device: BLEDevice, advertisement_data: Optional[AdvertisementData]) -> bool:
        """
        デバイスが実際のCO2計かどうかを判定
        
        Args:
            device: BLEデバイス
            advertisement_data: アドバタイズメントデータ
            
        Returns:
            実際のCO2計の場合True
        """
        if not advertisement_data:
            return False
        
        # 製造者データによる判定
        if hasattr(advertisement_data, 'manufacturer_data') and advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if manufacturer_id == cls.MANUFACTURER_ID and len(data) >= 16:
                    return True
        
        # サービスデータによる判定
        if hasattr(advertisement_data, 'service_data') and advertisement_data.service_data:
            for uuid in advertisement_data.service_data.keys():
                if str(uuid).lower() == cls.SERVICE_UUID.lower():
                    return True
        
        return False
    
    def parse_manufacturer_data(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        製造者データを解析
        
        Args:
            data: 製造者データ
            
        Returns:
            解析されたデータ、無効な場合はNone
        """
        if len(data) < 16:
            return None
        
        try:
            # CO2値: バイト13-14 (ビッグエンディアン)
            # 例: 02e7 = 743ppm, 02e8 = 744ppm
            co2_ppm = struct.unpack('>H', data[13:15])[0]
            
            # 温度・湿度の位置（精度解析に基づく改善）
            humidity = data[10] if len(data) > 10 else 0
            
            # 温度の高精度計算（小数点1桁対応）
            # 解析結果: バイト0を使用 (byte + 100) / 10
            # 例: 0xb0(176) + 100 = 276 → 276/10 = 27.6°C
            temperature_raw = data[0] if len(data) > 0 else 0
            temperature = (temperature_raw + 100) / 10.0
            
            # 現実的な温度範囲チェック (0-50°C)
            if temperature < 0 or temperature > 50:
                # フォールバック: 従来の方法
                temperature_raw_fallback = data[7] if len(data) > 7 else 0
                if temperature_raw_fallback > 70:
                    temperature = float(temperature_raw_fallback - 72)
                else:
                    temperature = float(temperature_raw_fallback)
            
            return {
                "co2_ppm": co2_ppm,
                "temperature": temperature,
                "humidity": float(humidity),
                "raw_data": data.hex()
            }
        except (struct.error, IndexError) as e:
            logger.error(f"製造者データ解析エラー: {e}")
            return None
    
    def parse_service_data(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        サービスデータを解析
        
        Args:
            data: サービスデータ
            
        Returns:
            解析されたデータ、無効な場合はNone
        """
        if len(data) < 3:
            return None
        
        try:
            # サービスデータ: 350064
            # 推測: 温度・湿度情報?
            return {
                "service_raw": data.hex(),
                "byte0": data[0],  # 53
                "byte1": data[1],  # 0
                "byte2": data[2],  # 100
            }
        except (IndexError) as e:
            logger.error(f"サービスデータ解析エラー: {e}")
            return None
    
    def create_sensor_data_from_advertisement(self, advertisement_data: AdvertisementData) -> Optional[CO2SensorData]:
        """
        ブロードキャストデータからCO2SensorDataオブジェクトを作成
        
        Args:
            advertisement_data: アドバタイズメントデータ
            
        Returns:
            CO2SensorDataオブジェクト、作成できない場合はNone
        """
        # 製造者データからメインデータを取得
        main_data = None
        if hasattr(advertisement_data, 'manufacturer_data') and advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if manufacturer_id == self.MANUFACTURER_ID:
                    main_data = self.parse_manufacturer_data(data)
                    break
        
        if not main_data:
            return None
        
        # サービスデータから追加情報を取得
        service_data = None
        if hasattr(advertisement_data, 'service_data') and advertisement_data.service_data:
            for uuid, data in advertisement_data.service_data.items():
                if str(uuid).lower() == self.SERVICE_UUID.lower():
                    service_data = self.parse_service_data(data)
                    break
        
        try:
            return CO2SensorData(
                timestamp=datetime.now(timezone.utc),
                co2_ppm=main_data["co2_ppm"],
                temperature=main_data["temperature"],
                humidity=main_data["humidity"],
                device_address=self.device_address,
                raw_data=main_data["raw_data"]
            )
        except Exception as e:
            logger.error(f"CO2SensorData作成エラー: {e}")
            return None
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        デバイス情報を取得
        
        Returns:
            デバイス情報の辞書
        """
        return {
            "name": self.device_name,
            "address": self.device_address,
            "manufacturer_id": self.MANUFACTURER_ID,
            "device_type_name": "Real CO2 Meter",
            "service_uuid": self.SERVICE_UUID
        }