#!/usr/bin/env python3
"""
SwitchBot CO2センサーの実際のデータを解析
"""

import struct

def analyze_switchbot_data():
    """実際のデータを解析"""
    # 実際のデータ
    hex_data = "1006361e0061a9c1"
    data = bytes.fromhex(hex_data)
    
    # 実際の値
    actual_co2 = 744
    actual_temp = 28.0
    actual_humidity = 59
    
    print(f"生データ: {hex_data}")
    print(f"バイト配列: {[f'{b:02x}' for b in data]}")
    print(f"10進数: {list(data)}")
    print()
    print(f"実際の値: CO2={actual_co2}ppm, 温度={actual_temp}°C, 湿度={actual_humidity}%")
    print("=" * 60)
    
    # 各バイト位置でのCO2値の候補を計算
    print("CO2値の候補:")
    for i in range(len(data) - 1):
        # リトルエンディアン
        co2_le = struct.unpack('<H', data[i:i+2])[0]
        # ビッグエンディアン
        co2_be = struct.unpack('>H', data[i:i+2])[0]
        # 単一バイト x 倍数
        co2_single = data[i]
        co2_x2 = data[i] * 2
        co2_x4 = data[i] * 4
        co2_x10 = data[i] * 10
        
        print(f"バイト{i}-{i+1}: LE={co2_le}, BE={co2_be}, 単体={co2_single}, x2={co2_x2}, x4={co2_x4}, x10={co2_x10}")
        if co2_le == actual_co2:
            print(f"  ★ CO2一致! リトルエンディアン バイト{i}-{i+1}")
        if co2_be == actual_co2:
            print(f"  ★ CO2一致! ビッグエンディアン バイト{i}-{i+1}")
        if co2_single == actual_co2:
            print(f"  ★ CO2一致! 単一バイト{i}")
        if co2_x2 == actual_co2:
            print(f"  ★ CO2一致! バイト{i} x2")
        if co2_x4 == actual_co2:
            print(f"  ★ CO2一致! バイト{i} x4")
        if co2_x10 == actual_co2:
            print(f"  ★ CO2一致! バイト{i} x10")
    
    print("\n温度の候補:")
    for i in range(len(data)):
        # 符号付き8ビット
        temp_signed = struct.unpack('b', data[i:i+1])[0]
        # 符号なし8ビット
        temp_unsigned = data[i]
        # 10倍されている場合
        temp_div10 = data[i] / 10.0
        # 温度オフセット
        temp_offset = data[i] - 100  # 仮定
        
        print(f"バイト{i}: 符号付き={temp_signed}, 符号なし={temp_unsigned}, /10={temp_div10}, -100={temp_offset}")
        if abs(temp_signed - actual_temp) < 1:
            print(f"  ★ 温度一致! 符号付きバイト{i}")
        if abs(temp_unsigned - actual_temp) < 1:
            print(f"  ★ 温度一致! 符号なしバイト{i}")
        if abs(temp_div10 - actual_temp) < 1:
            print(f"  ★ 温度一致! バイト{i}/10")
        if abs(temp_offset - actual_temp) < 1:
            print(f"  ★ 温度一致! バイト{i}-100")
    
    print("\n湿度の候補:")
    for i in range(len(data)):
        humidity = data[i]
        print(f"バイト{i}: {humidity}")
        if humidity == actual_humidity:
            print(f"  ★ 湿度一致! バイト{i}")
    
    print("\n16進数での特別なパターン:")
    # 744 = 0x2E8
    print(f"744 = 0x{744:04x}")
    # 28.0 (整数部分)
    print(f"28 = 0x{28:02x}")
    # 59
    print(f"59 = 0x{59:02x}")

if __name__ == "__main__":
    analyze_switchbot_data()