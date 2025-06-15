#!/usr/bin/env python3
"""
スマートCO2デバイス監視プログラム
OUI（会社固有番号）ベースの高精度自動検出
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from co2logger.core.oui_detector import OUIBasedCO2Detector, OUIDatabase
from co2logger.devices.real_co2_meter import RealCO2Meter
from co2logger.devices.switchbot_co2 import SwitchBotCO2Sensor
from co2logger import ConsoleExporter

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartCO2Monitor:
    """OUIベース高精度CO2デバイス監視"""
    
    def __init__(self):
        self.exporter = ConsoleExporter(verbose=True)
        self.oui_detector = OUIBasedCO2Detector()
        self.verified_co2_devices: Dict[str, str] = {}  # アドレス -> デバイスタイプ
        self.device_last_update: Dict[str, datetime] = {}
        self.update_interval = 30
        self.discovery_timeout = 60
        
    def should_update_device(self, device_address: str) -> bool:
        """デバイス更新が必要かチェック"""
        last_update = self.device_last_update.get(device_address)
        if last_update is None:
            return True
        
        elapsed = (datetime.now() - last_update).total_seconds()
        return elapsed >= self.update_interval
    
    def verify_co2_device(self, device: BLEDevice, advertisement_data: AdvertisementData) -> Optional[str]:
        """厳密なCO2デバイス検証"""
        
        # ステップ1: OUIベース事前フィルタリング
        if not self.oui_detector.is_likely_co2_device(device, advertisement_data):
            return None
        
        oui_info = OUIDatabase.get_oui_info(device.address)
        
        # ステップ2: 実際のCO2計検証
        if RealCO2Meter.is_real_co2_meter(device, advertisement_data):
            # OUI確認
            if oui_info and "co2_meter" in oui_info.get("device_types", []):
                # 追加検証: CO2値が現実的な範囲か
                if hasattr(advertisement_data, 'manufacturer_data'):
                    for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                        if manufacturer_id == 2409 and len(data) >= 16:
                            try:
                                import struct
                                co2_ppm = struct.unpack('>H', data[13:15])[0]
                                if 300 <= co2_ppm <= 5000:
                                    logger.info(f"✅ 実際のCO2計を確認: {device.address} (OUI: {OUIDatabase.extract_oui(device.address)})")
                                    return "real_co2_meter"
                            except:
                                pass
        
        # ステップ3: SwitchBot CO2センサー検証
        if SwitchBotCO2Sensor.is_co2_sensor(device, advertisement_data):
            # 追加のOUI検証は省略（SwitchBotは複数OUIを使用する可能性）
            logger.info(f"✅ SwitchBot CO2センサーを確認: {device.address} (OUI: {OUIDatabase.extract_oui(device.address)})")
            return "switchbot_co2"
        
        return None
    
    def process_co2_data(self, device: BLEDevice, advertisement_data: AdvertisementData, device_type: str):
        """CO2データを処理"""
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
                
                # データ出力
                asyncio.create_task(self.exporter.export(co2_data))
                
                # OUI情報付きログ
                oui = OUIDatabase.extract_oui(device.address)
                oui_info = OUIDatabase.get_oui_info(device.address)
                company = oui_info.get("company", "Unknown") if oui_info else "Unknown"
                
                logger.info(f"[{company}] {device.address} (OUI: {oui})")
                logger.info(f"  CO2: {co2_data.co2_ppm} ppm")
                logger.info(f"  温度: {co2_data.temperature}°C")
                logger.info(f"  湿度: {co2_data.humidity}%")
                
        except Exception as e:
            logger.error(f"CO2データ処理エラー ({device.address}): {e}")
    
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """高精度検出コールバック"""
        try:
            # OUIベース厳密検証
            device_type = self.verify_co2_device(device, advertisement_data)
            
            if device_type:
                # 新しいCO2デバイス発見
                if device.address not in self.verified_co2_devices:
                    self.verified_co2_devices[device.address] = device_type
                    
                    oui = OUIDatabase.extract_oui(device.address)
                    oui_info = OUIDatabase.get_oui_info(device.address)
                    company = oui_info.get("company", "Unknown") if oui_info else "Unknown"
                    confidence = OUIDatabase.get_confidence_level(device.address)
                    
                    device_type_name = {
                        "real_co2_meter": "実際のCO2計",
                        "switchbot_co2": "SwitchBot CO2センサー"
                    }.get(device_type, device_type)
                    
                    logger.info(f"🎯 高精度CO2デバイス発見: {device_type_name}")
                    logger.info(f"   アドレス: {device.address}")
                    logger.info(f"   OUI: {oui} ({company})")
                    logger.info(f"   信頼性: {confidence}")
                    logger.info(f"   デバイス名: {device.name or '(名前なし)'}")
                
                # データ更新チェック
                if self.should_update_device(device.address):
                    self.process_co2_data(device, advertisement_data, device_type)
            else:
                # 未知のOUIを調査
                suggestion = self.oui_detector.suggest_new_oui(device, advertisement_data)
                if suggestion:
                    logger.debug(f"🔍 新しいCO2デバイス候補: {suggestion['oui']} ({device.address})")
                    
        except Exception as e:
            logger.error(f"検出コールバックエラー: {e}")
    
    async def discovery_phase(self):
        """高精度発見フェーズ"""
        logger.info("🎯 OUIベース高精度CO2デバイス発見を開始...")
        logger.info(f"対象OUI: {list(OUIDatabase.CO2_DEVICE_OUIS.keys())}")
        logger.info(f"発見タイムアウト: {self.discovery_timeout}秒")
        
        scanner = BleakScanner(self.detection_callback)
        await scanner.start()
        await asyncio.sleep(self.discovery_timeout)
        await scanner.stop()
        
        if self.verified_co2_devices:
            logger.info(f"✅ {len(self.verified_co2_devices)}台の確実なCO2デバイスを発見:")
            for address, device_type in self.verified_co2_devices.items():
                oui = OUIDatabase.extract_oui(address)
                oui_info = OUIDatabase.get_oui_info(address)
                company = oui_info.get("company", "Unknown") if oui_info else "Unknown"
                
                device_type_name = {
                    "real_co2_meter": "実際のCO2計",
                    "switchbot_co2": "SwitchBot CO2センサー"
                }.get(device_type, device_type)
                
                logger.info(f"  📍 {address} - {device_type_name} ({company}, OUI: {oui})")
        else:
            logger.warning("⚠️  確実なCO2デバイスが見つかりませんでした")
            
            # 検出統計表示
            stats = self.oui_detector.get_detection_statistics()
            if stats["total_unknown"] > 0:
                logger.info(f"未知のOUI {stats['total_unknown']}個を検出:")
                for oui in stats["unknown_ouis"]:
                    logger.info(f"  - {oui}")
    
    async def monitoring_phase(self, duration: int = 300):
        """監視フェーズ"""
        if not self.verified_co2_devices:
            logger.info("監視する確実なCO2デバイスがありません")
            return
        
        logger.info("📡 高精度CO2デバイス監視を開始...")
        logger.info(f"監視デバイス数: {len(self.verified_co2_devices)}台")
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
    
    async def start_smart_monitoring(self, monitoring_duration: int = 300):
        """スマート監視開始"""
        logger.info("🚀 スマートCO2デバイス監視プログラム開始")
        
        # フェーズ1: 高精度発見
        await self.discovery_phase()
        
        if self.verified_co2_devices:
            # フェーズ2: 監視
            await self.monitoring_phase(monitoring_duration)
        else:
            logger.info("確実なCO2デバイスが見つからないため、監視を終了します")

async def main():
    """メイン関数"""
    print("=" * 70)
    print("🎯 スマートCO2デバイス監視プログラム")
    print("=" * 70)
    print("✨ 特徴:")
    print("  - OUI（会社固有番号）ベース高精度検出")
    print("  - 誤検出を大幅削減")
    print("  - 既知のCO2デバイスメーカーのみ対象")
    print("  - 30秒間隔でリアルタイム表示")
    print()
    print("🎯 対象OUI（会社固有番号）:")
    for oui, info in OUIDatabase.CO2_DEVICE_OUIS.items():
        print(f"  - {oui} : {info['company']} ({info['confidence']} confidence)")
    print("=" * 70)
    
    monitor = SmartCO2Monitor()
    await monitor.start_smart_monitoring()

if __name__ == "__main__":
    asyncio.run(main())