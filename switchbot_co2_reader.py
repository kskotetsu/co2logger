#!/usr/bin/env python3
"""
SwitchBot CO2センサー Bluetoothデータ読み取りプログラム
"""

import asyncio
import struct
import time
from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# SwitchBot 通信用の定数
SWITCHBOT_SERVICE_UUID = "cba20d00-224d-11e6-9fb8-0002a5d5c51b"
SWITCHBOT_WRITE_CHAR_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"
SWITCHBOT_NOTIFY_CHAR_UUID = "cba20003-224d-11e6-9fb8-0002a5d5c51b"

# SwitchBot CO2センサーのデバイスタイプ
SWITCHBOT_METER_PRO_CO2_TYPE = 0x7B  # 123 in decimal

class SwitchBotCO2Reader:
    def __init__(self):
        self.device = None
        self.client = None
        self.co2_data = {}
        
    async def scan_for_switchbot_devices(self, scan_time=10):
        """SwitchBotデバイスをスキャンする"""
        print(f"SwitchBotデバイスをスキャン中... ({scan_time}秒)")
        
        devices = await BleakScanner.discover(timeout=scan_time)
        switchbot_devices = []
        
        for device in devices:
            if device.name and "switchbot" in device.name.lower():
                switchbot_devices.append(device)
                print(f"発見されたSwitchBotデバイス: {device.name} ({device.address})")
        
        return switchbot_devices
    
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """アドバタイズメントデータからSwitchBot CO2センサーを検出"""
        if device.name and "switchbot" in device.name.lower():
            print(f"SwitchBotデバイス検出: {device.name} - {device.address}")
            
            # サービスデータをチェック
            if advertisement_data.service_data:
                for uuid, data in advertisement_data.service_data.items():
                    if len(data) > 0:
                        device_type = data[0] & 0x7F  # 下位7ビット
                        if device_type == SWITCHBOT_METER_PRO_CO2_TYPE:
                            print(f"CO2センサー発見: {device.name} ({device.address})")
                            self.device = device
                            return True
        return False
    
    async def scan_for_co2_sensor(self, scan_time=10):
        """CO2センサー専用のスキャン"""
        print(f"SwitchBot CO2センサーをスキャン中... ({scan_time}秒)")
        
        scanner = BleakScanner(detection_callback=self.detection_callback)
        await scanner.start()
        await asyncio.sleep(scan_time)
        await scanner.stop()
        
        return self.device
    
    async def connect_to_device(self, device):
        """デバイスに接続"""
        try:
            print(f"デバイスに接続中: {device.name} ({device.address})")
            self.client = BleakClient(device.address)
            await self.client.connect()
            print("接続成功!")
            return True
        except Exception as e:
            print(f"接続エラー: {e}")
            return False
    
    def notification_handler(self, sender, data):
        """通知データのハンドラー"""
        try:
            print(f"受信データ: {data.hex()}")
            self.parse_co2_data(data)
        except Exception as e:
            print(f"データ解析エラー: {e}")
    
    def parse_co2_data(self, data):
        """CO2データを解析"""
        if len(data) < 2:
            return
        
        try:
            # データ形式の解析（SwitchBot CO2センサー固有）
            # 実際のデータ構造は調査が必要
            timestamp = datetime.now()
            
            if len(data) >= 6:
                # 仮の解析ロジック - 実際のプロトコルに合わせて調整が必要
                co2_value = struct.unpack('<H', data[2:4])[0]  # CO2 ppm
                temperature = struct.unpack('<h', data[4:6])[0] / 10.0  # 温度
                
                self.co2_data = {
                    'timestamp': timestamp,
                    'co2_ppm': co2_value,
                    'temperature': temperature,
                    'raw_data': data.hex()
                }
                
                self.display_data()
            else:
                print(f"データが短すぎます: {data.hex()}")
                
        except Exception as e:
            print(f"データ解析エラー: {e}")
            print(f"生データ: {data.hex()}")
    
    def display_data(self):
        """データをコンソールに表示"""
        if self.co2_data:
            print("=" * 50)
            print(f"時刻: {self.co2_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"CO2濃度: {self.co2_data['co2_ppm']} ppm")
            print(f"温度: {self.co2_data['temperature']}°C")
            print(f"生データ: {self.co2_data['raw_data']}")
            print("=" * 50)
    
    async def start_monitoring(self):
        """監視を開始"""
        if not self.client or not self.client.is_connected:
            print("デバイスが接続されていません")
            return
        
        try:
            # 通知を有効化
            await self.client.start_notify(SWITCHBOT_NOTIFY_CHAR_UUID, self.notification_handler)
            print("データ監視を開始しました...")
            
            # 定期的にデータを要求（必要に応じて）
            while True:
                await asyncio.sleep(5)  # 5秒間隔
                try:
                    # データ要求コマンドを送信（プロトコルに依存）
                    # 実際のコマンドは調査が必要
                    request_cmd = bytes([0x01, 0x02, 0x03])  # 仮のコマンド
                    await self.client.write_gatt_char(SWITCHBOT_WRITE_CHAR_UUID, request_cmd)
                except Exception as e:
                    print(f"データ要求エラー: {e}")
                
        except Exception as e:
            print(f"監視エラー: {e}")
    
    async def disconnect(self):
        """デバイスから切断"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("デバイスから切断しました")

async def main():
    """メイン処理"""
    reader = SwitchBotCO2Reader()
    
    try:
        # Step 1: デバイスをスキャン
        device = await reader.scan_for_co2_sensor(scan_time=10)
        
        if not device:
            print("SwitchBot CO2センサーが見つかりませんでした")
            # 一般的なSwitchBotデバイスもスキャン
            devices = await reader.scan_for_switchbot_devices(scan_time=10)
            if devices:
                print("発見されたSwitchBotデバイス:")
                for i, dev in enumerate(devices):
                    print(f"{i+1}. {dev.name} ({dev.address})")
                
                # 最初のデバイスを選択
                device = devices[0]
            else:
                print("SwitchBotデバイスが見つかりませんでした")
                return
        
        # Step 2: デバイスに接続
        if await reader.connect_to_device(device):
            # Step 3: データ監視を開始
            await reader.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n監視を停止しています...")
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        await reader.disconnect()

if __name__ == "__main__":
    asyncio.run(main())