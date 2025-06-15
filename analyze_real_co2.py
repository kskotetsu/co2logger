#!/usr/bin/env python3
"""
実際のCO2計 (B0:E9:FE:58:74:AE) のデータ解析
"""

import asyncio
import logging
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_co2_data(hex_data: str):
    """CO2計の生データを解析"""
    data = bytes.fromhex(hex_data)
    
    print(f"\n=== CO2計データ解析: {hex_data} ===")
    print(f"データ長: {len(data)} バイト")
    print(f"バイト配列: {[f'{b:02x}' for b in data]}")
    print(f"10進数: {list(data)}")
    
    # 実測値と照合するため各種パターンを試行
    print("\n--- CO2値候補 (744ppm目標) ---")
    for i in range(len(data) - 1):
        # 2バイト組み合わせ
        be_val = (data[i] << 8) | data[i+1]
        le_val = (data[i+1] << 8) | data[i]
        
        print(f"バイト{i}-{i+1}: BE={be_val}, LE={le_val}")
        if be_val == 744:
            print(f"  ★ CO2一致! ビッグエンディアン バイト{i}-{i+1}")
        if le_val == 744:
            print(f"  ★ CO2一致! リトルエンディアン バイト{i}-{i+1}")
    
    # 単一バイトでの候補
    print("\n--- 単一バイト候補 ---")
    for i, byte_val in enumerate(data):
        for multiplier in [1, 2, 4, 8, 10]:
            result = byte_val * multiplier
            if 700 <= result <= 800:  # 744付近
                print(f"バイト{i}({byte_val}) × {multiplier} = {result}")
    
    # 特殊計算
    print("\n--- 特殊計算パターン ---")
    if len(data) >= 16:
        # 16進数の特殊パターンを探す
        # 744 = 0x2E8
        target_hex = "2e8"
        hex_str = hex_data.lower()
        if target_hex in hex_str:
            pos = hex_str.find(target_hex)
            print(f"744(0x2E8)が位置{pos//2}で発見: {target_hex}")

class RealCO2Monitor:
    """実際のCO2計を監視"""
    
    def __init__(self):
        self.target_address = "B0:E9:FE:58:74:AE"
        self.detected_data = set()
        
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """実際のCO2計のデータを収集"""
        if device.address.upper() != self.target_address.upper():
            return
        
        print(f"\n[実際のCO2計検出] {device.address}")
        print(f"RSSI: {advertisement_data.rssi}")
        
        # 製造者データ
        if hasattr(advertisement_data, 'manufacturer_data') and advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                hex_data = data.hex()
                if hex_data not in self.detected_data:
                    self.detected_data.add(hex_data)
                    print(f"製造者ID: {manufacturer_id}")
                    print(f"生データ: {hex_data}")
                    analyze_co2_data(hex_data)
        
        # サービスデータ
        if hasattr(advertisement_data, 'service_data') and advertisement_data.service_data:
            print("サービスデータ:")
            for uuid, data in advertisement_data.service_data.items():
                hex_data = data.hex()
                print(f"  UUID: {uuid}, データ: {hex_data}")
                if hex_data and hex_data not in self.detected_data:
                    self.detected_data.add(hex_data)
                    analyze_co2_data(hex_data)
    
    async def start_monitoring(self, duration: int = 60):
        """監視開始"""
        print(f"実際のCO2計を監視: {self.target_address}")
        print(f"監視時間: {duration}秒")
        
        try:
            scanner = BleakScanner(self.detection_callback)
            await scanner.start()
            await asyncio.sleep(duration)
            await scanner.stop()
        except Exception as e:
            logger.error(f"監視エラー: {e}")
        finally:
            print(f"\n検出されたデータパターン数: {len(self.detected_data)}")

async def main():
    """メイン関数"""
    print("=== 実際のCO2計データ解析 ===")
    print("実機表示値: 744ppm, 28°C, 59%")
    print("目標: 生データから正確な値を抽出")
    
    # 既知データの解析
    print("\n--- 既知データの解析 ---")
    known_data = "b0e9fe5874ae3464009c3b001102e800"
    analyze_co2_data(known_data)
    
    # リアルタイム監視
    print("\n--- リアルタイム監視 ---")
    monitor = RealCO2Monitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())