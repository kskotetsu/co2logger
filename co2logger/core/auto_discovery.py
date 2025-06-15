#!/usr/bin/env python3
"""
CO2デバイス自動検出機能
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from ..devices.real_co2_meter import RealCO2Meter
from ..devices.switchbot_co2 import SwitchBotCO2Sensor

logger = logging.getLogger(__name__)


class CO2DeviceDiscovery:
    """CO2デバイス自動検出クラス"""
    
    def __init__(self):
        self.discovered_devices: Dict[str, Tuple[BLEDevice, str]] = {}  # アドレス -> (デバイス, タイプ)
        
    def detect_co2_device_type(self, device: BLEDevice, advertisement_data: AdvertisementData) -> Optional[str]:
        """CO2デバイスのタイプを検出"""
        
        # 実際のCO2計をチェック
        if RealCO2Meter.is_real_co2_meter(device, advertisement_data):
            # 追加検証: CO2値が現実的な範囲か
            if hasattr(advertisement_data, 'manufacturer_data'):
                for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                    if manufacturer_id == 2409 and len(data) >= 16:
                        try:
                            import struct
                            co2_ppm = struct.unpack('>H', data[13:15])[0]
                            if 300 <= co2_ppm <= 5000:
                                return "real_co2_meter"
                        except:
                            pass
        
        # SwitchBot CO2センサーをチェック
        if SwitchBotCO2Sensor.is_co2_sensor(device, advertisement_data):
            return "switchbot_co2"
        
        # その他のCO2デバイス候補
        if device.name and 'co2' in device.name.lower():
            return "generic_co2"
        
        return None
    
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """デバイス検出コールバック"""
        device_type = self.detect_co2_device_type(device, advertisement_data)
        
        if device_type and device.address not in self.discovered_devices:
            self.discovered_devices[device.address] = (device, device_type)
            device_type_name = {
                "real_co2_meter": "実際のCO2計",
                "switchbot_co2": "SwitchBot CO2センサー",
                "generic_co2": "汎用CO2デバイス"
            }.get(device_type, device_type)
            
            logger.info(f"CO2デバイス発見: {device_type_name} ({device.address})")
    
    async def discover_co2_devices(self, scan_time: float = 60.0) -> List[Tuple[BLEDevice, str]]:
        """
        CO2デバイスを自動発見
        
        Args:
            scan_time: スキャン時間（秒）
            
        Returns:
            発見されたCO2デバイスのリスト [(デバイス, タイプ), ...]
        """
        logger.info(f"CO2デバイス自動発見開始 ({scan_time}秒間)")
        
        self.discovered_devices.clear()
        
        try:
            scanner = BleakScanner(self.detection_callback)
            await scanner.start()
            await asyncio.sleep(scan_time)
            await scanner.stop()
        except Exception as e:
            logger.error(f"スキャンエラー: {e}")
        
        devices = list(self.discovered_devices.values())
        logger.info(f"発見完了: {len(devices)}台のCO2デバイス")
        
        return devices
    
    async def find_best_co2_device(self, scan_time: float = 60.0) -> Optional[Tuple[BLEDevice, str]]:
        """
        最適なCO2デバイスを1台選択
        
        Args:
            scan_time: スキャン時間（秒）
            
        Returns:
            最適なCO2デバイス (デバイス, タイプ) または None
        """
        devices = await self.discover_co2_devices(scan_time)
        
        if not devices:
            return None
        
        # 優先順位: 実際のCO2計 > SwitchBot CO2センサー > その他
        priority = {
            "real_co2_meter": 1,
            "switchbot_co2": 2,
            "generic_co2": 3
        }
        
        # 優先順位でソート
        devices.sort(key=lambda x: priority.get(x[1], 999))
        
        best_device, device_type = devices[0]
        device_type_name = {
            "real_co2_meter": "実際のCO2計",
            "switchbot_co2": "SwitchBot CO2センサー",
            "generic_co2": "汎用CO2デバイス"
        }.get(device_type, device_type)
        
        logger.info(f"最適なCO2デバイスを選択: {device_type_name} ({best_device.address})")
        
        return best_device, device_type


class AutoCO2DeviceManager:
    """自動検出されたCO2デバイス管理クラス"""
    
    def __init__(self):
        self.discovery = CO2DeviceDiscovery()
        self.active_devices: Dict[str, object] = {}  # アドレス -> デバイスオブジェクト
        
    async def setup_auto_devices(self, scan_time: float = 60.0) -> int:
        """
        CO2デバイスを自動セットアップ
        
        Args:
            scan_time: スキャン時間（秒）
            
        Returns:
            セットアップされたデバイス数
        """
        devices = await self.discovery.discover_co2_devices(scan_time)
        
        self.active_devices.clear()
        
        for ble_device, device_type in devices:
            try:
                if device_type == "real_co2_meter":
                    device_obj = RealCO2Meter(ble_device)
                elif device_type == "switchbot_co2":
                    device_obj = SwitchBotCO2Sensor(ble_device)
                else:
                    continue  # 未対応タイプはスキップ
                
                self.active_devices[ble_device.address] = device_obj
                logger.info(f"CO2デバイスセットアップ完了: {ble_device.address}")
                
            except Exception as e:
                logger.error(f"デバイスセットアップエラー ({ble_device.address}): {e}")
        
        return len(self.active_devices)
    
    def get_active_devices(self) -> Dict[str, object]:
        """アクティブなCO2デバイス一覧を取得"""
        return self.active_devices.copy()