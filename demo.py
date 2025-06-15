#!/usr/bin/env python3
"""
ライブラリのデモンストレーション（シミュレーションモード）
"""

import asyncio
import random
from datetime import datetime, timezone

# 新しいライブラリをインポート
from co2logger import (
    CO2SensorData,
    ConsoleExporter,
    JsonFileExporter,
    HttpSender
)


async def generate_demo_data():
    """デモ用のCO2センサーデータを生成"""
    # リアルなCO2データをシミュレート
    base_co2 = random.randint(400, 1200)  # 400-1200 ppm
    temperature = random.uniform(18.0, 28.0)  # 18-28℃
    humidity = random.uniform(40.0, 70.0)  # 40-70%
    
    return CO2SensorData(
        timestamp=datetime.now(timezone.utc),
        co2_ppm=base_co2,
        temperature=round(temperature, 1),
        humidity=round(humidity, 1),
        device_address="AA:BB:CC:DD:EE:FF",
        raw_data=f"demo_data_{random.randint(1000, 9999)}"
    )


async def demo_console_export():
    """コンソールエクスポートのデモ"""
    print("\n" + "="*60)
    print("コンソールエクスポーターのデモ")
    print("="*60)
    
    exporter = ConsoleExporter(verbose=True)
    
    # 複数のデータを生成してエクスポート
    for i in range(3):
        data = await generate_demo_data()
        await exporter.export(data)
        await asyncio.sleep(1)


async def demo_json_export():
    """JSONファイルエクスポートのデモ"""
    print("\n" + "="*60)
    print("JSONファイルエクスポーターのデモ")
    print("="*60)
    
    exporter = JsonFileExporter("/tmp/demo_co2_data.json", append_mode=True)
    
    # データを生成してエクスポート
    data_list = []
    for i in range(5):
        data = await generate_demo_data()
        data_list.append(data)
    
    # 一括でエクスポート
    await exporter.export(data_list)
    print(f"5件のデータを /tmp/demo_co2_data.json に保存しました")
    
    # ファイルの内容を確認
    try:
        with open("/tmp/demo_co2_data.json", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"ファイルサイズ: {len(content)} 文字")
            print("ファイルの最初の200文字:")
            print(content[:200] + "..." if len(content) > 200 else content)
    except Exception as e:
        print(f"ファイル読み取りエラー: {e}")


async def demo_http_export():
    """HTTP送信エクスポートのデモ（モック）"""
    print("\n" + "="*60)
    print("HTTP送信エクスポーターのデモ")
    print("="*60)
    
    # テスト用のHTTPエンドポイント（存在しない）
    sender = HttpSender("http://localhost:8080/api/co2-data", timeout=5.0, max_retries=2)
    
    # 認証ヘッダーを追加
    sender.set_authentication("Bearer", "demo_token_12345")
    sender.add_headers({
        "X-Device-ID": "switchbot_demo_001",
        "X-Location": "office"
    })
    
    # データを生成
    data = await generate_demo_data()
    
    print(f"送信先URL: {sender.url}")
    print(f"ヘッダー: {sender.headers}")
    print(f"送信データ: CO2={data.co2_ppm}ppm, 温度={data.temperature}°C")
    
    # 送信を試行（失敗することが予想される）
    result = await sender.export(data)
    
    if result:
        print("✅ HTTP送信成功")
    else:
        print("❌ HTTP送信失敗（予想通り - デモ環境のため）")


async def demo_data_models():
    """データモデルのデモ"""
    print("\n" + "="*60)
    print("データモデルのデモ")
    print("="*60)
    
    # CO2センサーデータを作成
    data = await generate_demo_data()
    
    print("作成されたCO2センサーデータ:")
    print(f"  文字列表現: {data}")
    print(f"  辞書形式: {data.to_dict()}")
    
    # 辞書からデータを復元
    dict_data = data.to_dict()
    restored_data = CO2SensorData.from_dict(dict_data)
    
    print(f"  復元後のデータ: {restored_data}")
    print(f"  元データと同じか: {data == restored_data}")


async def demo_real_time_simulation():
    """リアルタイムデータシミュレーション"""
    print("\n" + "="*60)
    print("リアルタイムデータ監視シミュレーション")
    print("="*60)
    print("5秒間隔でデータを生成・表示します（Ctrl+Cで停止）")
    
    console_exporter = ConsoleExporter(verbose=False)
    json_exporter = JsonFileExporter("/tmp/realtime_co2_data.json", append_mode=True)
    
    try:
        count = 0
        while count < 10:  # 10回で自動停止
            # データを生成
            data = await generate_demo_data()
            
            # コンソールに表示
            await console_exporter.export(data)
            
            # JSONファイルに保存
            await json_exporter.export(data)
            
            count += 1
            print(f"[{count}/10] 次のデータまで5秒...")
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        print("\n監視を停止しました")
    
    print(f"\n{count}件のデータを /tmp/realtime_co2_data.json に保存しました")


async def main():
    """メインデモ関数"""
    print("SwitchBot CO2センサーライブラリ デモンストレーション")
    print("="*60)
    print("このデモでは、実際のBluetoothデバイスなしでライブラリの機能を確認できます")
    
    # 各機能のデモを実行
    await demo_data_models()
    await demo_console_export()
    await demo_json_export()
    await demo_http_export()
    
    # リアルタイムシミュレーション
    print("\nリアルタイムシミュレーションを開始しますか？ (y/n): ", end="")
    # デモなので自動的にyesとして実行
    print("y")
    await demo_real_time_simulation()
    
    print("\n" + "="*60)
    print("デモンストレーション完了！")
    print("実際の使用時は main.py を実行し、SwitchBot CO2センサーを接続してください")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nデモを終了します")
    except Exception as e:
        print(f"デモ実行エラー: {e}")
        import traceback
        traceback.print_exc()