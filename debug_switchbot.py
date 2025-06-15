#!/usr/bin/env python3
"""
SwitchBot CO2センサーの詳細データ解析デバッグ
"""

import asyncio
import logging
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_switchbot_data(hex_data: str):
    """SwitchBotデータの詳細解析"""
    data = bytes.fromhex(hex_data)
    
    print(f"\n=== データ解析: {hex_data} ===")
    print(f"バイト配列: {[f'{b:02x}' for b in data]}")
    print(f"10進数: {list(data)}")
    
    # GitHubスクリプト方式: 2バイトペアで解析
    print("\n--- 2バイトペア解析 ---")
    values = []
    for i in range(0, min(8, len(data)), 2):
        if i + 1 < len(data):
            # ビッグエンディアン
            value_be = (data[i] << 8) | data[i+1]
            # リトルエンディアン
            value_le = (data[i+1] << 8) | data[i]
            values.append(value_be)
            print(f"ペア{i//2}: バイト{i}-{i+1} = 0x{data[i]:02x}{data[i+1]:02x} = BE:{value_be}, LE:{value_le}")
    
    print(f"\nペア値: {values}")
    
    # 各値の候補を計算
    print("\n--- CO2候補 ---")
    co2_candidates = []
    
    # パターン1: 各ペア値をそのまま
    for i, val in enumerate(values):
        if 300 <= val <= 5000:
            co2_candidates.append((f"ペア{i}", val))
            print(f"ペア{i} = {val} (範囲内)")
        else:
            print(f"ペア{i} = {val} (範囲外)")
    
    # パターン2: 下位バイト * 倍数
    for i, val in enumerate(values):
        low_byte = val & 0xFF
        for multiplier in [1, 2, 4, 8, 10]:
            result = low_byte * multiplier
            if 300 <= result <= 5000:
                co2_candidates.append((f"ペア{i}_下位x{multiplier}", result))
                print(f"ペア{i}下位({low_byte}) x {multiplier} = {result}")
    
    # パターン3: 特殊計算
    if len(values) >= 3:
        val_97 = values[2] & 0xFF
        special_calc = val_97 * 8 - 32
        if 300 <= special_calc <= 5000:
            co2_candidates.append((f"特殊計算({val_97}*8-32)", special_calc))
            print(f"特殊計算: {val_97} * 8 - 32 = {special_calc}")
    
    print(f"\nCO2候補: {co2_candidates}")
    
    # 温度・湿度候補
    print("\n--- 温度・湿度候補 ---")
    for i, byte_val in enumerate(data):
        print(f"バイト{i}: {byte_val} (温度候補: {byte_val}°C, 湿度候補: {byte_val}%)")
        if byte_val > 100:
            adjusted = byte_val - 38
            print(f"  調整湿度: {byte_val} - 38 = {adjusted}%")

async def monitor_switchbot():
    """SwitchBotデバイスを監視してデータを解析"""
    detected_data = set()
    
    def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
        if hasattr(advertisement_data, 'manufacturer_data') and advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if manufacturer_id == 76:  # SwitchBot
                    hex_data = data.hex()
                    if hex_data not in detected_data:
                        detected_data.add(hex_data)
                        print(f"\n新しいSwitchBotデータ検出: {device.address}")
                        analyze_switchbot_data(hex_data)
    
    print("SwitchBotデバイスを監視中... (10秒間)")
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(10)
    await scanner.stop()
    
    print(f"\n検出されたデータパターン数: {len(detected_data)}")

if __name__ == "__main__":
    # 既知のデータを解析
    print("=== 既知データの解析 ===")
    analyze_switchbot_data("1006361e0061a9c1")
    
    # リアルタイム監視
    print("\n=== リアルタイム監視 ===")
    asyncio.run(monitor_switchbot())