#!/usr/bin/env python3
"""
SwitchBot CO2センサーの表示値とBluetoothデータの照合確認
"""

def analyze_readings():
    """データ解析結果と実際の表示値を比較"""
    
    print("=== SwitchBot CO2センサー データ照合 ===")
    print()
    
    # 検出されたデータ
    detected_readings = [
        {
            "device": "49:4B:91:4B:53:83",
            "raw_data": "1006361e0061a9c1", 
            "parsed_co2": 4102,
            "parsed_temp": 30.0,
            "parsed_humidity": 97.0
        },
        {
            "device": "5D:D9:01:F8:B3:17",
            "raw_data": "10063e1e2ad19c0d",
            "parsed_co2": 4102, 
            "parsed_temp": 30.0,
            "parsed_humidity": 100.0
        }
    ]
    
    print("検出されたBluetoothデータ:")
    for i, reading in enumerate(detected_readings, 1):
        print(f"\nデバイス{i}: {reading['device']}")
        print(f"  生データ: {reading['raw_data']}")
        print(f"  解析結果: CO2={reading['parsed_co2']}ppm, 温度={reading['parsed_temp']}°C, 湿度={reading['parsed_humidity']}%")
    
    print("\n" + "="*60)
    print("【確認してください】")
    print("1. 実際のSwitchBot CO2センサーの液晶画面の表示値は？")
    print("   - CO2: _____ ppm")
    print("   - 温度: _____ °C") 
    print("   - 湿度: _____ %")
    print()
    print("2. 複数のSwitchBotデバイスがありますか？")
    print("   - 検出された2つのデバイスのうち、どちらが目的のCO2センサーですか？")
    print()
    print("3. 表示値が4102ppmの場合（異常に高い値）:")
    print("   - センサーの校正が必要な可能性")
    print("   - 別のSwitchBotデバイス（CO2センサー以外）の可能性")
    print()
    print("4. 表示値が744ppm前後の場合:")
    print("   - データ構造の解析が必要")
    print("   - 別の計算式やエンコード方式")
    
    # 4102ppmが正しい場合の分析
    print("\n" + "="*60)
    print("【4102ppmが正しい場合】")
    print("この値は室内CO2濃度としては異常に高いです：")
    print("- 通常の室内: 400-1000ppm")
    print("- 換気不良: 1000-3000ppm")  
    print("- 危険レベル: 5000ppm以上")
    print("- 4102ppm = かなり換気が必要なレベル")
    
    # データ構造の可能性
    print("\n【データ構造の他の可能性】")
    data1 = bytes.fromhex("1006361e0061a9c1")
    data2 = bytes.fromhex("10063e1e2ad19c0d")
    
    print("特殊計算パターン:")
    print(f"バイト5 * 7.67 = {data1[5]} * 7.67 = {data1[5] * 7.67:.0f}")
    print(f"(バイト5 + バイト6) / 2 = ({data1[5]} + {data1[6]}) / 2 = {(data1[5] + data1[6]) / 2:.0f}")
    print(f"バイト5 + バイト6*2 = {data1[5]} + {data1[6]}*2 = {data1[5] + data1[6]*2}")

if __name__ == "__main__":
    analyze_readings()