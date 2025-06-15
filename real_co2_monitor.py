#!/usr/bin/env python3
"""
実際のCO2計 (B0:E9:FE:58:74:AE) 専用監視プログラム
"""

import asyncio
import logging
from datetime import datetime
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from co2logger.devices.real_co2_meter import RealCO2Meter
from co2logger import ConsoleExporter

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealCO2Monitor:
    """実際のCO2計専用監視クラス"""
    
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
        """実際のCO2計のデータを検出"""
        try:
            # 目的のデバイスアドレスのみ処理
            if device.address.upper() != self.target_address:
                return
            
            # 更新間隔チェック
            if not self.should_update():
                return
            
            # 実際のCO2計かチェック
            if not RealCO2Meter.is_real_co2_meter(device, advertisement_data):
                return
            
            # データ解析・表示
            meter = RealCO2Meter(device)
            co2_data = meter.create_sensor_data_from_advertisement(advertisement_data)
            
            if co2_data:
                # 更新時刻記録
                self.last_update = datetime.now()
                
                # データを出力
                asyncio.create_task(self.exporter.export(co2_data))
                
                # 詳細ログ
                logger.info(f"[実際のCO2計] {device.address}")
                logger.info(f"  CO2: {co2_data.co2_ppm} ppm")
                logger.info(f"  温度: {co2_data.temperature}°C")
                logger.info(f"  湿度: {co2_data.humidity}%")
                logger.info(f"  生データ: {co2_data.raw_data}")
            
        except Exception as e:
            logger.error(f"検出エラー: {e}")
    
    async def start_monitoring(self, duration: int = 300):
        """指定時間だけ監視"""
        logger.info(f"実際のCO2計を監視開始: {self.target_address}")
        logger.info("製造者ID: 2409, CO2値位置: バイト13-14")
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
    print("=== 実際のCO2計 専用監視プログラム ===")
    print("デバイス: B0:E9:FE:58:74:AE")
    print("製造者ID: 2409")
    print("CO2値: バイト13-14 (ビッグエンディアン)")
    print()
    
    monitor = RealCO2Monitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())