#!/usr/bin/env python3
"""
実際のCO2計の温度データ精度解析
小数点1桁の精度を実現するための解析
"""

import struct

def analyze_temperature_precision():
    """温度データの精度解析"""
    
    # 実際のデータサンプル
    samples = [
        {
            "raw_data": "b0e9fe5874ae3664009c3b001102e700",
            "actual_temp": 28.0,  # 実機表示温度
            "co2": 743
        }
    ]
    
    print("=== 温度精度解析 ===")
    
    for i, sample in enumerate(samples):
        print(f"\nサンプル {i+1}:")
        data = bytes.fromhex(sample["raw_data"])
        actual_temp = sample["actual_temp"]
        
        print(f"実機温度: {actual_temp}°C")
        print(f"生データ: {sample['raw_data']}")
        print(f"バイト配列: {[f'{b:02x}' for b in data]}")
        
        # 各バイトを温度候補として詳細解析
        for j, byte_val in enumerate(data):
            print(f"\nバイト{j} (0x{byte_val:02x} = {byte_val}):")
            
            # パターン1: そのまま使用
            if abs(byte_val - actual_temp) < 5:
                print(f"  直接使用: {byte_val} ≈ {actual_temp} (差: {abs(byte_val - actual_temp)})")
            
            # パターン2: 10倍されている（小数点1桁）
            temp_div10 = byte_val / 10.0
            if abs(temp_div10 - actual_temp) < 5:
                print(f"  ÷10: {temp_div10} ≈ {actual_temp} (差: {abs(temp_div10 - actual_temp)})")
            
            # パターン3: オフセット付き
            for offset in [-100, -72, -50, -32, -20, +20, +50]:
                temp_offset = byte_val + offset
                if abs(temp_offset - actual_temp) < 2:
                    print(f"  +{offset}: {temp_offset} ≈ {actual_temp} (差: {abs(temp_offset - actual_temp)})")
                
                # オフセット後の10倍値
                temp_offset_div10 = temp_offset / 10.0
                if abs(temp_offset_div10 - actual_temp) < 2:
                    print(f"  (+{offset})÷10: {temp_offset_div10} ≈ {actual_temp} (差: {abs(temp_offset_div10 - actual_temp)})")
        
        # 2バイト組み合わせでの温度候補
        print(f"\n2バイト組み合わせ:")
        for j in range(len(data) - 1):
            # ビッグエンディアン
            temp_be = struct.unpack('>H', data[j:j+2])[0]
            # リトルエンディアン  
            temp_le = struct.unpack('<H', data[j:j+2])[0]
            
            # 10倍、100倍で割った値
            for divisor in [10, 100, 1000]:
                temp_be_div = temp_be / divisor
                temp_le_div = temp_le / divisor
                
                if abs(temp_be_div - actual_temp) < 2:
                    print(f"  バイト{j}-{j+1} BE÷{divisor}: {temp_be_div} ≈ {actual_temp}")
                if abs(temp_le_div - actual_temp) < 2:
                    print(f"  バイト{j}-{j+1} LE÷{divisor}: {temp_le_div} ≈ {actual_temp}")

def test_current_calculation():
    """現在の計算方式をテスト"""
    print("\n=== 現在の計算方式テスト ===")
    
    data = bytes.fromhex("b0e9fe5874ae3664009c3b001102e700")
    
    # 現在の実装
    temperature_raw = data[7]  # バイト7 = 0x64 = 100
    current_temp = temperature_raw - 72  # 100 - 72 = 28
    
    print(f"現在の実装:")
    print(f"  バイト7: {temperature_raw} (0x{temperature_raw:02x})")
    print(f"  計算: {temperature_raw} - 72 = {current_temp}°C")
    print(f"  結果: 整数のみ（小数点なし）")
    
    # 改善案: より精密な計算
    print(f"\n改善案:")
    
    # 案1: サービスデータから温度を取得
    print("  案1: サービスデータ '350064' を解析")
    service_data = bytes.fromhex("350064")
    if len(service_data) >= 3:
        # バイト2 = 100 = 10.0度?
        temp_candidate = service_data[2] / 10.0
        print(f"    サービスデータバイト2 ÷ 10 = {temp_candidate}°C")
    
    # 案2: 製造者データの別バイト
    print("  案2: 製造者データの別バイトを精査")
    for i in range(len(data)):
        val = data[i]
        # 280 (28.0°C の10倍) に近い値を探す
        if 250 <= val <= 350:  # 25.0°C - 35.0°C の範囲
            temp_precise = val / 10.0
            print(f"    バイト{i}: {val} → {temp_precise}°C")

if __name__ == "__main__":
    analyze_temperature_precision()
    test_current_calculation()