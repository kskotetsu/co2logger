# CO2 Logger - CO2センサー Bluetooth監視システム

CO2センサーからBluetoothでデータを読み取り、リアルタイムで監視・記録するPythonライブラリです。

![GitHub License](https://img.shields.io/github/license/kskotetsu/co2logger)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-69%20passed-green)

## 🚀 特徴

- **自動デバイス検出**: OUI（会社固有番号）ベースの高精度検出
- **リアルタイム監視**: ブロードキャスト受信時に即座表示
- **高精度温度計算**: 線形関係による小数点1桁対応
- **データエクスポート**: コンソール・JSON・HTTP API対応
- **TDD設計**: 69個のテストによる品質保証
- **モジュラー設計**: 拡張可能なライブラリ構造

## 📋 必要環境

### システム要件
- Python 3.10以上
- Bluetooth対応デバイス
- Linux/Windows（WSLでは制限あり）

### 対応デバイス
- CO2センサー（OUI: B0:E9:FE）
- 製造者ID: 2409のBLEデバイス

## 🔧 インストール

```bash
# リポジトリをクローン
git clone https://github.com/kskotetsu/co2logger.git
cd co2logger

# UVパッケージマネージャーでセットアップ（推奨）
uv sync

# または pip でインストール
pip install -e .
```

## 🎯 使い方

### 基本的な使用方法

```bash
# 自動検出CO2監視（推奨）
uv run python smart_co2_monitor.py

# シミュレーションデモ（BLE未対応環境）
uv run python demo.py

# 手動デバイス指定監視
uv run python main.py
```

### プログラムでの使用

```python
import asyncio
from co2logger.core.auto_discovery import CO2DeviceDiscovery
from co2logger.devices.real_co2_meter import RealCO2Meter
from co2logger import ConsoleExporter

async def main():
    # CO2デバイス自動検出
    discovery = CO2DeviceDiscovery()
    device, device_type = await discovery.find_best_co2_device()
    
    if device and device_type == "real_co2_meter":
        # CO2計接続
        meter = RealCO2Meter(device)
        
        # データエクスポーター設定
        exporter = ConsoleExporter(verbose=True)
        
        # ブロードキャストデータからCO2データ取得
        # （実際の使用では BleakScanner を使用）
        print(f"CO2デバイス発見: {device.address}")

asyncio.run(main())
```

## 📊 データエクスポート機能

### 1. コンソール出力
```python
from co2logger import ConsoleExporter

exporter = ConsoleExporter(verbose=True)
await exporter.export(sensor_data)
```

### 2. JSONファイル出力
```python
from co2logger import JsonFileExporter

exporter = JsonFileExporter("/path/to/output.json", append_mode=True)
await exporter.export(sensor_data)
```

### 3. HTTP API送信
```python
from co2logger import HttpSender

sender = HttpSender("https://api.example.com/co2-data")
sender.set_authentication("Bearer", "your_token")
await sender.export(sensor_data)
```

## 🧪 テスト実行

包括的なテストスイートを実行：

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=co2logger

# 特定テスト実行
uv run pytest tests/models/test_sensor_data.py -v
```

## 📁 プロジェクト構造

```
co2logger/
├── co2logger/              # メインライブラリ
│   ├── models/             # データモデル
│   ├── core/               # コア機能（OUI検出・自動検出）
│   ├── devices/            # デバイス固有クラス
│   └── exporters/          # データエクスポート機能
├── tests/                  # テストスイート（69テスト）
├── smart_co2_monitor.py    # 自動検出監視プログラム（推奨）
├── main.py                 # 手動指定監視プログラム
├── demo.py                 # シミュレーションデモ
└── README.md              # このファイル
```

## 📄 データ形式

### CO2センサーデータ

```json
{
  "timestamp": "2025-06-15T06:37:52.950485+00:00",
  "device_address": "B0:E9:FE:XX:XX:XX",
  "co2_ppm": 812,
  "temperature": 27.8,
  "humidity": 60,
  "raw_data": "b0e9fe5874ae4664089b3c0011032c00"
}
```

### データ解析技術

- **CO2値**: バイト13-14（ビッグエンディアン）
- **温度**: バイト9使用の線形関係 `温度 = 0.2 * byte9 - 3.2`
- **湿度**: バイト10（整数値）

## 🔍 OUIベース検出

本システムは OUI（Organizationally Unique Identifier）を使用してCO2デバイスを識別：

- **対象OUI**: `B0:E9:FE`（CO2センサーメーカー）
- **製造者ID**: 2409
- **信頼性**: 高精度（誤検出を大幅削減）

## ⚙️ 設定オプション

### 監視設定
- **発見タイムアウト**: 30秒（変更可能）
- **更新方式**: ブロードキャスト受信時に即座表示
- **対象**: 最初に発見されたOUI一致デバイスのみ

### 温度計算設定
```python
# 高精度線形関係
temperature = 0.2 * raw_byte9 - 3.2

# フォールバック方式（範囲外の場合）
if temperature < 0 or temperature > 50:
    temperature = fallback_calculation(raw_data)
```

## 🔧 開発・貢献

### ブランチ戦略
- `main`: 安定版
- `feature/*`: 新機能開発

### コミット規約
```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
test: テスト追加・修正
refactor: リファクタリング
```

### 貢献手順
1. フォークを作成
2. フィーチャーブランチを作成 `git checkout -b feature/AmazingFeature`
3. 変更をコミット `git commit -m 'feat: 素晴らしい新機能追加'`
4. ブランチにプッシュ `git push origin feature/AmazingFeature`
5. プルリクエストを作成

## 🛠️ 対応環境

### 動作確認済み
- Windows 10/11（Bluetooth対応）
- Linux（BlueZ対応）
- macOS（Bluetooth対応）

### 制限事項
- WSL環境ではBluetooth機能が制限される
- 通信距離は約10m以内を推奨
- 同時接続デバイス数に制限あり

## 🔒 プライバシー保護

- 個人のMACアドレス情報は含まれていません
- OUI情報（会社識別子）のみを使用
- セキュアなデバイス検出を実装

## 📜 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルをご覧ください。

## 🙏 謝辞

- [bleak](https://github.com/hbldh/bleak) - Python Bluetooth Low Energy ライブラリ
- Bluetooth SIG - OUI仕様とBLE規格
- CO2センサーメーカー - デバイス技術提供

## 📞 サポート

問題や質問がある場合：

1. [Issues](https://github.com/kskotetsu/co2logger/issues)で既存の問題を確認
2. 新しいIssueを作成
3. 詳細な環境情報と再現手順を含めてください

---

**注意**: このライブラリは CO2センサーの非公式実装です。メーカーの保証対象外での使用となります。