#!/usr/bin/env python3
"""
SwitchBot CO2センサーのみを特定して監視
他のSwitchBotデバイスを除外
"""

import asyncio
import logging
from datetime import datetime, timezone
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from co2logger import SwitchBotCO2Sensor, ConsoleExporter

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CO2SensorFilter:
    """CO2センサーのみをフィルタリングするクラス"""
    
    def __init__(self):
        self.exporter = ConsoleExporter(verbose=True)
        self.device_cache = {}  # アドレス -> 最後の更新時刻
        self.co2_devices = set()  # 確認済みCO2センサーのアドレス
        self.update_interval = 30  # 30秒間隔で更新表示
        
    def is_valid_co2_sensor(self, manufacturer_id: int, data: bytes) -> bool:
        """CO2センサーとして有効なデバイスかチェック"""
        if manufacturer_id != 76 or len(data) < 8:
            return False
        
        device_type = data[0] & 0x7F
        if device_type != 0x10:  # 実測でのCO2センサータイプ
            return False
        
        # CO2値が現実的な範囲かチェック
        byte5_val = data[5]
        co2_calc = int(byte5_val * 7.67)
        if not (300 <= co2_calc <= 5000):
            return False
        
        # 温度が現実的な範囲かチェック
        temp = data[3]
        if not (0 <= temp <= 50):
            return False
        
        return True
    
    def should_update_device(self, device_address: str) -> bool:
        """デバイスの更新が必要かチェック"""
        now = datetime.now()
        last_update = self.device_cache.get(device_address)
        
        if last_update is None:
            return True
        
        elapsed = (now - last_update).total_seconds()
        return elapsed >= self.update_interval
    
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """CO2センサーのみを検出するコールバック"""
        try:
            if not hasattr(advertisement_data, 'manufacturer_data'):
                return
            
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if self.is_valid_co2_sensor(manufacturer_id, data):
                    # 更新間隔チェック
                    if not self.should_update_device(device.address):
                        continue
                    
                    # CO2センサーとして記録
                    self.co2_devices.add(device.address)
                    self.device_cache[device.address] = datetime.now()
                    
                    # データ解析・表示
                    sensor = SwitchBotCO2Sensor(device)
                    co2_data = sensor.create_sensor_data_from_advertisement(advertisement_data)
                    
                    if co2_data:
                        # データを出力
                        asyncio.create_task(self.exporter.export(co2_data))
                        logger.info(f"[CO2センサー] {device.address} - "
                                   f"CO2: {co2_data.co2_ppm}ppm, "
                                   f"温度: {co2_data.temperature}°C, "
                                   f"湿度: {co2_data.humidity}%")
                    break
        except Exception as e:
            logger.error(f"検出エラー: {e}")
    
    async def start_monitoring(self, duration: int = 300):
        """指定時間だけ監視（デフォルト5分）"""
        logger.info("SwitchBot CO2センサーのみを監視開始...")
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
            logger.info(f"監視終了 - 検出されたCO2センサー: {len(self.co2_devices)}台")
            for addr in self.co2_devices:
                logger.info(f"  CO2センサー: {addr}")

async def main():
    """メイン関数"""
    filter_monitor = CO2SensorFilter()
    await filter_monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())