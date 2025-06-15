# プライバシー保護のためのリポジトリクリーンアップ手順

## 実行されたクリーンアップ

### 1. 削除されたファイル
- `real_co2_monitor.py` - 個人のMACアドレスを含んでいたファイル
- `analyze_real_co2.py` - 個人のMACアドレスを含んでいたファイル  
- `target_co2_sensor.py` - 個人のMACアドレスを含んでいたファイル
- `analyze_temperature.py` - 個人のMACアドレスを含んでいたファイル

### 2. 修正されたファイル
- `co2logger/devices/real_co2_meter.py` - コメント内のMACアドレスをOUI情報のみに変更

### 3. GitHubリポジトリの完全置換推奨

個人情報がコミット履歴に残っているため、以下の手順でリポジトリを完全に置き換えることを推奨します：

```bash
# 1. 現在のリポジトリをバックアップ
git clone https://github.com/kskotetsu/co2logger.git co2logger-backup

# 2. GitHubでリポジトリを削除・再作成

# 3. クリーンなブランチをプッシュ
git push origin clean-history:main --force

# 4. 新しいリポジトリとして扱う
git branch -D master
git checkout -b main
```

## セキュリティ向上

- OUI情報（B0:E9:FE）のみを保持
- 個人のMACアドレス情報を完全削除
- プライバシー保護を強化
- 汎用的なCO2デバイス検出コードとして再構築

## 残存機能

- CO2デバイス自動検出（OUIベース）
- リアルタイムモニタリング
- 高精度温度計算
- データエクスポート機能
- TDDによるテストスイート