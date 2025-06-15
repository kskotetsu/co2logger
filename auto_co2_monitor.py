#!/usr/bin/env python3
"""
CO2計自動検出・監視プログラム
MACアドレス事前指定なしで自動的にCO2デバイスを発見
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from co2logger.devices.real_co2_meter import RealCO2Meter
from co2logger.devices.switchbot_co2 import SwitchBotCO2Sensor
from co2logger import ConsoleExporter

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoCO2Monitor:
    """CO2デバイス自動検出・監視クラス"""
    
    def __init__(self):
        self.exporter = ConsoleExporter(verbose=True)
        self.detected_co2_devices: Dict[str, str] = {}  # アドレス -> デバイスタイプ
        self.device_last_update: Dict[str, datetime] = {}
        self.update_interval = 30  # 30秒間隔
        self.discovery_mode = True
        self.discovery_timeout = 60  # 60秒間スキャンしてデバイス発見
        
    def should_update_device(self, device_address: str) -> bool:
        """デバイスの更新が必要かチェック"""
        last_update = self.device_last_update.get(device_address)
        if last_update is None:
            return True
        
        elapsed = (datetime.now() - last_update).total_seconds()
        return elapsed >= self.update_interval
    
    def detect_co2_device_type(self, device: BLEDevice, advertisement_data: AdvertisementData) -> Optional[str]:
        """CO2デバイスのタイプを自動検出"""
        
        # 1. 実際のCO2計（製造者ID: 2409）をチェック
        if RealCO2Meter.is_real_co2_meter(device, advertisement_data):
            # CO2値が現実的な範囲かダブルチェック
            if hasattr(advertisement_data, 'manufacturer_data'):
                for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                    if manufacturer_id == 2409 and len(data) >= 16:
                        try:
                            import struct
                            co2_ppm = struct.unpack('>H', data[13:15])[0]
                            if 300 <= co2_ppm <= 5000:  # 現実的なCO2範囲
                                return "real_co2_meter"
                        except:
                            pass
        
        # 2. SwitchBot CO2センサー（製造者ID: 76）をチェック
        if SwitchBotCO2Sensor.is_co2_sensor(device, advertisement_data):
            return "switchbot_co2"
        
        # 3. その他のCO2デバイス候補をチェック
        if hasattr(advertisement_data, 'manufacturer_data'):
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                # CO2関連と思われるデータパターンをチェック
                if len(data) >= 8:
                    # デバイス名にCO2が含まれる
                    if device.name and 'co2' in device.name.lower():
                        return "unknown_co2"
        
        return None
    
    def process_co2_data(self, device: BLEDevice, advertisement_data: AdvertisementData, device_type: str):
        """CO2データを処理して表示"""
        try:
            co2_data = None
            
            if device_type == "real_co2_meter":
                meter = RealCO2Meter(device)
                co2_data = meter.create_sensor_data_from_advertisement(advertisement_data)
            elif device_type == "switchbot_co2":
                sensor = SwitchBotCO2Sensor(device)
                co2_data = sensor.create_sensor_data_from_advertisement(advertisement_data)
            
            if co2_data:
                # 更新時刻記録
                self.device_last_update[device.address] = datetime.now()
                
                # データを出力
                asyncio.create_task(self.exporter.export(co2_data))
                
                # 詳細ログ
                device_type_name = {
                    "real_co2_meter": "実際のCO2計",
                    "switchbot_co2": "SwitchBot CO2センサー",
                    "unknown_co2": "不明なCO2デバイス"
                }.get(device_type, device_type)
                
                logger.info(f"[{device_type_name}] {device.address}")
                logger.info(f"  CO2: {co2_data.co2_ppm} ppm")
                logger.info(f"  温度: {co2_data.temperature}°C")
                logger.info(f"  湿度: {co2_data.humidity}%")
                
        except Exception as e:
            logger.error(f"CO2データ処理エラー ({device.address}): {e}")
    
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """デバイス検出コールバック"""
        try:
            # CO2デバイスタイプを自動検出
            device_type = self.detect_co2_device_type(device, advertisement_data)
            
            if device_type:
                # 新しいCO2デバイスを発見
                if device.address not in self.detected_co2_devices:
                    self.detected_co2_devices[device.address] = device_type
                    device_type_name = {
                        "real_co2_meter": "実際のCO2計",
                        "switchbot_co2": "SwitchBot CO2センサー",
                        "unknown_co2": "不明なCO2デバイス"
                    }.get(device_type, device_type)
                    
                    logger.info(f"🔍 新しいCO2デバイスを発見: {device_type_name}")
                    logger.info(f"   アドレス: {device.address}")
                    logger.info(f"   デバイス名: {device.name or '(名前なし)'}")
                
                # 更新間隔チェック
                if self.should_update_device(device.address):
                    self.process_co2_data(device, advertisement_data, device_type)
                    
        except Exception as e:
            logger.error(f"検出コールバックエラー: {e}")
    
    async def discovery_phase(self):
        """CO2デバイス発見フェーズ"""
        logger.info("🔍 CO2デバイス自動発見を開始...")
        logger.info(f"発見タイムアウト: {self.discovery_timeout}秒")
        
        scanner = BleakScanner(self.detection_callback)
        await scanner.start()
        await asyncio.sleep(self.discovery_timeout)
        await scanner.stop()
        
        if self.detected_co2_devices:
            logger.info(f"✅ {len(self.detected_co2_devices)}台のCO2デバイスを発見:")
            for address, device_type in self.detected_co2_devices.items():
                device_type_name = {
                    "real_co2_meter": "実際のCO2計",
                    "switchbot_co2": "SwitchBot CO2センサー",
                    "unknown_co2": "不明なCO2デバイス"
                }.get(device_type, device_type)
                logger.info(f"  📍 {address} - {device_type_name}")
        else:
            logger.warning("⚠️  CO2デバイスが見つかりませんでした")
            logger.info("以下を確認してください:")
            logger.info("1. CO2デバイスの電源が入っているか")
            logger.info("2. Bluetoothが有効になっているか")
            logger.info("3. デバイスが近くにあるか")
    
    async def monitoring_phase(self, duration: int = 300):
        """監視フェーズ"""
        if not self.detected_co2_devices:
            logger.info("監視するCO2デバイスがありません")
            return
        
        logger.info("📡 CO2デバイス監視を開始...")
        logger.info(f"監視デバイス数: {len(self.detected_co2_devices)}台")
        logger.info(f"更新間隔: {self.update_interval}秒")
        logger.info(f"監視時間: {duration}秒")
        logger.info("Ctrl+C で終了")
        
        try:
            scanner = BleakScanner(self.detection_callback)
            await scanner.start()
            await asyncio.sleep(duration)
            await scanner.stop()
        except KeyboardInterrupt:
            logger.info("ユーザーによる中断")
        except Exception as e:
            logger.error(f"監視エラー: {e}")
        finally:
            logger.info("監視終了")
    
    async def start_auto_monitoring(self, monitoring_duration: int = 300):
        """自動検出・監視を開始"""
        logger.info("🚀 CO2計自動検出・監視プログラム開始")
        
        # フェーズ1: デバイス発見
        await self.discovery_phase()
        
        if self.detected_co2_devices:
            # フェーズ2: 監視
            await self.monitoring_phase(monitoring_duration)
        else:
            logger.info("発見されたCO2デバイスがないため、監視を終了します")

async def main():
    """メイン関数"""
    print("=" * 60)
    print("🌍 CO2計自動検出・監視プログラム")
    print("=" * 60)
    print("✨ 特徴:")
    print("  - MACアドレス事前指定不要")
    print("  - 複数メーカーのCO2デバイス対応")
    print("  - 自動検出・自動監視")
    print("  - 30秒間隔でリアルタイム表示")
    print()
    print("🔍 対応デバイス:")
    print("  - 実際のCO2計 (製造者ID: 2409)")
    print("  - SwitchBot CO2センサー (製造者ID: 76)")
    print("  - その他のCO2デバイス")
    print("=" * 60)
    
    monitor = AutoCO2Monitor()
    await monitor.start_auto_monitoring()

if __name__ == "__main__":
    asyncio.run(main())