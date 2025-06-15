#!/usr/bin/env python3
"""
SwitchBot CO2センサー ブロードキャスト監視プログラム
接続不要でアドバタイズメントデータから直接CO2データを取得
"""

import asyncio
import logging
import signal
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

class CO2BroadcastMonitor:
    """CO2センサーのブロードキャスト監視クラス"""
    
    def __init__(self):
        self.running = False
        self.exporter = ConsoleExporter(verbose=True)
        self.detected_sensors = {}  # アドレス -> SwitchBotCO2Sensor
        
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """デバイス検出時のコールバック"""
        try:
            # CO2センサーかどうかチェック
            if SwitchBotCO2Sensor.is_co2_sensor(device, advertisement_data):
                # 既知のセンサーでなければ作成
                if device.address not in self.detected_sensors:
                    logger.info(f"新しいCO2センサーを検出: {device.name} ({device.address})")
                    self.detected_sensors[device.address] = SwitchBotCO2Sensor(device)
                
                # ブロードキャストデータからCO2データを取得
                sensor = self.detected_sensors[device.address]
                co2_data = sensor.create_sensor_data_from_advertisement(advertisement_data)
                
                if co2_data:
                    # データを出力
                    asyncio.create_task(self.exporter.export(co2_data))
                    logger.info(f"CO2データ取得: {co2_data.co2_ppm} ppm, "
                               f"{co2_data.temperature}°C, {co2_data.humidity}%")
                else:
                    logger.debug(f"CO2データの解析に失敗: {device.address}")
        except Exception as e:
            logger.error(f"検出コールバックエラー: {e}")
    
    async def start_monitoring(self):
        """監視を開始"""
        logger.info("CO2センサーのブロードキャスト監視を開始します...")
        logger.info("Ctrl+C で終了してください")
        
        self.running = True
        
        try:
            scanner = BleakScanner(self.detection_callback)
            await scanner.start()
            
            # 監視継続
            while self.running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("監視が中断されました")
        except Exception as e:
            logger.error(f"監視エラー: {e}")
        finally:
            try:
                await scanner.stop()
            except:
                pass
            logger.info("監視を終了しました")
    
    def stop_monitoring(self):
        """監視を停止"""
        self.running = False

async def main():
    """メイン関数"""
    logger.info("SwitchBot CO2センサー ブロードキャスト監視プログラム")
    logger.info("=" * 50)
    
    monitor = CO2BroadcastMonitor()
    
    # シグナルハンドラー設定
    def signal_handler(signum, frame):
        logger.info("終了シグナルを受信しました")
        monitor.stop_monitoring()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("キーボード割り込みで終了します")
    except Exception as e:
        logger.error(f"プログラムエラー: {e}")
    
    logger.info("プログラムを終了します")

if __name__ == "__main__":
    asyncio.run(main())