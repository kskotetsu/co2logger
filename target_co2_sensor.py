#!/usr/bin/env python3
"""
特定のCO2センサーのみを監視
"""

import asyncio
import logging
from datetime import datetime, timezone
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from co2logger import SwitchBotCO2Sensor, ConsoleExporter

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TargetCO2Monitor:
    """特定のCO2センサーのみを監視"""
    
    def __init__(self, target_address: str = "B0:E9:FE:58:74:AE"):
        self.target_address = target_address.upper()
        self.exporter = ConsoleExporter(verbose=True)
        self.last_update = None
        self.update_interval = 30  # 30秒間隔
        
    def should_update(self) -> bool:
        """更新が必要かチェック"""
        if self.last_update is None:
            return True
        
        elapsed = (datetime.now() - self.last_update).total_seconds()
        return elapsed >= self.update_interval
    
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """目的のCO2センサーのみを検出"""
        try:
            # 目的のデバイスアドレスのみ処理
            if device.address.upper() != self.target_address:
                return
            
            # 更新間隔チェック
            if not self.should_update():
                return
            
            # 製造者データチェック
            if not hasattr(advertisement_data, 'manufacturer_data'):
                return
            
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if manufacturer_id == 2409 and len(data) >= 8:  # 実際のCO2計の製造者ID
                    # データ構造を解析する必要がある
                    # 生データ: b0e9fe5874ae3464009c3b001102e800
                        # データ解析・表示
                        sensor = SwitchBotCO2Sensor(device)
                        co2_data = sensor.create_sensor_data_from_advertisement(advertisement_data)
                        
                        if co2_data:
                            # 更新時刻記録
                            self.last_update = datetime.now()
                            
                            # データを出力
                            asyncio.create_task(self.exporter.export(co2_data))
                            
                            # 詳細ログ
                            logger.info(f"[目的のCO2センサー] {device.address}")
                            logger.info(f"  CO2: {co2_data.co2_ppm} ppm")
                            logger.info(f"  温度: {co2_data.temperature}°C")
                            logger.info(f"  湿度: {co2_data.humidity}%")
                            logger.info(f"  生データ: {co2_data.raw_data}")
                        break
        except Exception as e:
            logger.error(f"検出エラー: {e}")
    
    async def start_monitoring(self, duration: int = 300):
        """指定時間だけ監視"""
        logger.info(f"目的のCO2センサーを監視開始: {self.target_address}")
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

async def main():
    """メイン関数"""
    print("=== SwitchBot CO2センサー ターゲット監視 ===")
    print("検出されたCO2センサー候補:")
    print("1. 49:4B:91:4B:53:83 (743ppm表示)")
    print("2. 5D:D9:01:F8:B3:17")
    print()
    
    # デフォルトは743ppmを表示していたデバイス
    target = "49:4B:91:4B:53:83"
    
    monitor = TargetCO2Monitor(target)
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())