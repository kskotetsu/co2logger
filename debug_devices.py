#!/usr/bin/env python3
"""
Bluetoothデバイスのデバッグ用プログラム
検出されたすべてのデバイスの詳細情報を表示
"""

import asyncio
import logging
from bleak import BleakScanner, BLEDevice
from bleak.backends.scanner import AdvertisementData

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_scan():
    """すべてのBluetoothデバイスをスキャンしてデバッグ情報を表示"""
    print("=== Bluetoothデバイスデバッグスキャン開始 ===")
    print("10秒間スキャンします...")
    
    detected_devices = []
    
    def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
        """デバイス検出時のコールバック"""
        detected_devices.append((device, advertisement_data))
        
        print(f"\n--- デバイス {len(detected_devices)} ---")
        print(f"名前: {device.name}")
        print(f"アドレス: {device.address}")
        print(f"RSSI: {advertisement_data.rssi}")
        
        # サービスUUID
        if advertisement_data.service_uuids:
            print(f"サービスUUID: {advertisement_data.service_uuids}")
        
        # サービスデータ
        if advertisement_data.service_data:
            print("サービスデータ:")
            for uuid, data in advertisement_data.service_data.items():
                print(f"  UUID: {uuid}, データ: {data.hex()}")
        
        # 製造者データ
        if advertisement_data.manufacturer_data:
            print("製造者データ:")
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                print(f"  製造者ID: {manufacturer_id}, データ: {data.hex()}")
        
        # ローカル名
        if advertisement_data.local_name:
            print(f"ローカル名: {advertisement_data.local_name}")
        
        print("-" * 50)
    
    # コールバック付きスキャン
    try:
        scanner = BleakScanner(detection_callback)
        await scanner.start()
        await asyncio.sleep(10)
        await scanner.stop()
    except Exception as e:
        print(f"スキャンエラー: {e}")
        return
    
    print(f"\n=== スキャン完了: {len(detected_devices)}個のデバイスを検出 ===")
    
    # SwitchBot関連のデバイスを特定
    switchbot_candidates = []
    for device, ad_data in detected_devices:
        is_candidate = False
        reasons = []
        
        # 名前チェック
        if device.name and ("switchbot" in device.name.lower() or "co2" in device.name.lower()):
            is_candidate = True
            reasons.append(f"名前: {device.name}")
        
        # サービスUUIDチェック
        if ad_data.service_uuids:
            for uuid in ad_data.service_uuids:
                if "fee7" in uuid.lower() or "cba20d00" in uuid.lower():
                    is_candidate = True
                    reasons.append(f"サービスUUID: {uuid}")
        
        # サービスデータチェック
        if ad_data.service_data:
            for uuid, data in ad_data.service_data.items():
                if "fee7" in str(uuid).lower():
                    is_candidate = True
                    reasons.append(f"サービスデータ: {uuid}")
        
        if is_candidate:
            switchbot_candidates.append((device, ad_data, reasons))
    
    print(f"\n=== SwitchBot候補デバイス: {len(switchbot_candidates)}個 ===")
    for i, (device, ad_data, reasons) in enumerate(switchbot_candidates):
        print(f"\n候補 {i+1}:")
        print(f"  名前: {device.name}")
        print(f"  アドレス: {device.address}")
        print(f"  判定理由: {', '.join(reasons)}")

if __name__ == "__main__":
    asyncio.run(debug_scan())