#!/usr/bin/env python3
"""
新しいライブラリを使用したSwitchBot CO2センサー読み取りプログラム
"""

import asyncio
import logging
from datetime import datetime, timezone

# 新しいライブラリをインポート
from co2logger import (
    DeviceScanner, 
    SwitchBotCO2Sensor, 
    ConsoleExporter,
    JsonFileExporter
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """メイン処理"""
    logger.info("SwitchBot CO2センサー読み取りプログラムを開始")
    
    # エクスポーターを設定
    console_exporter = ConsoleExporter(verbose=True)
    json_exporter = JsonFileExporter("/tmp/co2_data.json", append_mode=True)
    
    try:
        # Step 1: デバイススキャナーを作成
        scanner = DeviceScanner()
        
        # Step 2: SwitchBotデバイスをスキャン
        logger.info("SwitchBotデバイスをスキャン中...")
        devices = await scanner.scan_for_switchbot_devices(scan_time=10)
        
        if not devices:
            logger.warning("SwitchBotデバイスが見つかりませんでした")
            print("デバイスが見つかりませんでした。以下を確認してください:")
            print("1. SwitchBot CO2センサーの電源が入っているか")
            print("2. Bluetoothが有効になっているか") 
            print("3. デバイスが近くにあるか")
            return
        
        # Step 3: CO2センサーを探す
        co2_sensor = None
        for device in devices:
            # CO2センサーかどうかチェック
            if SwitchBotCO2Sensor.is_co2_sensor(device, None):
                co2_sensor = SwitchBotCO2Sensor(device)
                logger.info(f"CO2センサーを発見: {device.name} ({device.address})")
                break
        
        if not co2_sensor:
            # 最初のSwitchBotデバイスを試す
            logger.info(f"CO2センサーが見つからなかったため、最初のデバイスを試します: {devices[0].name}")
            co2_sensor = SwitchBotCO2Sensor(devices[0])
        
        # Step 4: デバイス情報を表示
        device_info = co2_sensor.get_device_info()
        print(f"\n接続対象デバイス: {device_info['name']} ({device_info['address']})")
        
        # Step 5: デバイスに接続
        logger.info("デバイスに接続中...")
        if not await co2_sensor.connect():
            logger.error("デバイスへの接続に失敗しました")
            return
        
        print("接続成功！")
        
        # Step 6: データコールバックを設定
        async def data_callback(sensor_data):
            """データ受信時のコールバック"""
            # コンソールに出力
            await console_exporter.export(sensor_data)
            
            # JSONファイルに保存
            await json_exporter.export(sensor_data)
        
        co2_sensor.set_data_callback(data_callback)
        
        # Step 7: データ監視を開始
        logger.info("データ監視を開始...")
        await co2_sensor.start_monitoring()
        
        print("\nデータ監視中... (Ctrl+Cで停止)")
        print("=" * 60)
        
        # Step 8: 定期的にデータを要求
        try:
            while True:
                # 現在のデータを取得（新しいデータを要求）
                current_data = await co2_sensor.get_current_data(request_new=True, timeout=10.0)
                
                if current_data:
                    # データが取得できた場合は何もしない（コールバックで処理済み）
                    pass
                else:
                    print("データの取得に失敗またはタイムアウト")
                
                # 30秒待機
                await asyncio.sleep(30)
                
        except KeyboardInterrupt:
            print("\n\n監視を停止しています...")
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        print(f"エラー: {e}")
        
    finally:
        # Step 9: 接続を切断
        if 'co2_sensor' in locals() and co2_sensor:
            try:
                await co2_sensor.stop_monitoring()
                await co2_sensor.disconnect()
                logger.info("デバイスから切断しました")
                print("デバイスから切断しました")
            except Exception as e:
                logger.error(f"切断エラー: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nプログラムを終了します")
    except Exception as e:
        print(f"予期しないエラー: {e}")
        logger.error(f"予期しないエラー: {e}", exc_info=True)