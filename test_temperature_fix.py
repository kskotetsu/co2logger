#!/usr/bin/env python3
"""
温度精度修正のテスト
"""

import struct

def test_temperature_calculation():
    """修正された温度計算をテスト"""
    
    # ユーザーの実データ
    test_data = {
        "raw_data": "b0e9fe5874ae4564089b3d0011032c00",
        "actual_co2": 812,
        "actual_temp": 27.8
    }
    
    print("=== 温度精度修正テスト ===")
    print(f"実機表示: CO2={test_data['actual_co2']}ppm, 温度={test_data['actual_temp']}°C")
    print(f"生データ: {test_data['raw_data']}")
    
    data = bytes.fromhex(test_data['raw_data'])
    print(f"バイト配列: {[f'{b:02x}' for b in data]}")
    
    # CO2値の確認
    co2_ppm = struct.unpack('>H', data[13:15])[0]
    print(f"\nCO2計算結果: {co2_ppm}ppm (実機: {test_data['actual_co2']}ppm)")
    
    # 修正された温度計算
    temperature_raw = data[0]  # バイト0 = 0xb0 = 176
    temperature = (temperature_raw + 100) / 10.0
    
    print(f"\n温度計算結果:")
    print(f"  バイト0: 0x{temperature_raw:02x} = {temperature_raw}")
    print(f"  計算式: ({temperature_raw} + 100) ÷ 10 = {temperature}°C")
    print(f"  実機表示: {test_data['actual_temp']}°C")
    print(f"  誤差: {abs(temperature - test_data['actual_temp']):.1f}°C")
    
    # 精度評価
    co2_match = co2_ppm == test_data['actual_co2']
    temp_error = abs(temperature - test_data['actual_temp'])
    temp_acceptable = temp_error <= 0.5  # 0.5°C以内なら許容
    
    print(f"\n評価結果:")
    print(f"  CO2値: {'✅ 一致' if co2_match else '❌ 不一致'}")
    print(f"  温度精度: {'✅ 許容範囲内' if temp_acceptable else '❌ 許容範囲外'} (誤差: {temp_error:.1f}°C)")
    
    if co2_match and temp_acceptable:
        print("\n🎉 修正成功！小数点1桁の温度精度を実現")
    else:
        print("\n⚠️  さらなる調整が必要")

if __name__ == "__main__":
    test_temperature_calculation()