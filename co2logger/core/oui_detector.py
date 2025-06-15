#!/usr/bin/env python3
"""
Bluetooth OUI (Organizationally Unique Identifier) ベースのCO2デバイス検出
"""

import logging
from typing import Dict, List, Optional, Set
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

logger = logging.getLogger(__name__)


class OUIDatabase:
    """Bluetooth OUI データベース"""
    
    # 既知のCO2デバイスメーカーのOUI（実際のCO2計のみ）
    CO2_DEVICE_OUIS = {
        # 実際のCO2計のOUI（確実にCO2計と判明しているもののみ）
        "B0:E9:FE": {
            "company": "CO2計メーカー",
            "device_types": ["co2_meter"],
            "manufacturer_id": 2409,
            "confidence": "high"
        },
        
        # 注意: SwitchBotは除外
        # 理由: SwitchBotには温湿度計、スイッチ、カーテンなど
        #       CO2センサー以外のデバイスが多数存在するため
        #       OUIだけでは正確なCO2デバイス特定が困難
        
        # 将来、新しい確実なCO2専用メーカーが見つかったら追加
    }
    
    # 確実にCO2デバイスではないOUI（除外リスト）
    EXCLUDED_OUIS = {
        "00:00:00",  # 無効なOUI
        "FF:FF:FF",  # ブロードキャスト
        # スマートフォンなどの一般的なOUI
        "AC:DE:48",  # Apple
        "20:02:AF",  # Apple
        "38:F9:D3",  # Apple
        "B4:F0:AB",  # Apple
        # SwitchBot関連OUI（CO2センサー以外のデバイスが多いため除外）
        "74:8A:32",  # SwitchBot（温湿度計、スイッチ等含む）
        "4A:ED:3F",  # SwitchBot（カーテン、プラグ等含む）
        "69:FB:B8",  # SwitchBot（その他デバイス）
        # 他の非CO2デバイス
    }
    
    @classmethod
    def extract_oui(cls, mac_address: str) -> str:
        """MACアドレスからOUIを抽出"""
        return mac_address[:8].upper()
    
    @classmethod
    def is_known_co2_oui(cls, mac_address: str) -> bool:
        """既知のCO2デバイスOUIかチェック"""
        oui = cls.extract_oui(mac_address)
        return oui in cls.CO2_DEVICE_OUIS
    
    @classmethod
    def is_excluded_oui(cls, mac_address: str) -> bool:
        """除外対象のOUIかチェック"""
        oui = cls.extract_oui(mac_address)
        return oui in cls.EXCLUDED_OUIS
    
    @classmethod
    def get_oui_info(cls, mac_address: str) -> Optional[Dict]:
        """OUI情報を取得"""
        oui = cls.extract_oui(mac_address)
        return cls.CO2_DEVICE_OUIS.get(oui)
    
    @classmethod
    def get_confidence_level(cls, mac_address: str) -> str:
        """信頼性レベルを取得"""
        oui_info = cls.get_oui_info(mac_address)
        if oui_info:
            return oui_info.get("confidence", "unknown")
        return "unknown"


class OUIBasedCO2Detector:
    """OUIベースのCO2デバイス検出器"""
    
    def __init__(self):
        self.detected_ouis: Set[str] = set()
        self.unknown_ouis: Set[str] = set()
        
    def analyze_device_by_oui(self, device: BLEDevice, advertisement_data: AdvertisementData) -> Dict:
        """OUIベースでデバイスを解析"""
        mac_address = device.address
        oui = OUIDatabase.extract_oui(mac_address)
        
        analysis = {
            "mac_address": mac_address,
            "oui": oui,
            "is_known_co2": OUIDatabase.is_known_co2_oui(mac_address),
            "is_excluded": OUIDatabase.is_excluded_oui(mac_address),
            "oui_info": OUIDatabase.get_oui_info(mac_address),
            "confidence": OUIDatabase.get_confidence_level(mac_address),
            "device_name": device.name,
            "rssi": advertisement_data.rssi if advertisement_data else None
        }
        
        # 統計収集
        if analysis["is_known_co2"]:
            self.detected_ouis.add(oui)
        elif not analysis["is_excluded"]:
            self.unknown_ouis.add(oui)
        
        return analysis
    
    def is_likely_co2_device(self, device: BLEDevice, advertisement_data: AdvertisementData) -> bool:
        """CO2デバイスの可能性が高いかチェック"""
        analysis = self.analyze_device_by_oui(device, advertisement_data)
        
        # 確実に除外
        if analysis["is_excluded"]:
            return False
        
        # 既知のCO2デバイスOUI
        if analysis["is_known_co2"]:
            logger.debug(f"既知のCO2デバイスOUI検出: {analysis['oui']} ({device.address})")
            return True
        
        # 追加検証: 製造者データとOUIの組み合わせ
        if hasattr(advertisement_data, 'manufacturer_data') and advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                # 実際のCO2計: OUI B0:E9:FE + 製造者ID 2409
                if analysis["oui"] == "B0:E9:FE" and manufacturer_id == 2409:
                    logger.info(f"OUI+製造者IDでCO2計確認: {device.address}")
                    return True
                
                # SwitchBot: OUI + 製造者ID 76 + CO2データパターン
                if manufacturer_id == 76 and len(data) >= 8:
                    device_type = data[0] & 0x7F
                    if device_type == 0x10:  # CO2センサータイプ
                        logger.info(f"SwitchBot CO2センサー確認: {device.address}")
                        return True
        
        return False
    
    def get_detection_statistics(self) -> Dict:
        """検出統計を取得"""
        return {
            "known_co2_ouis": list(self.detected_ouis),
            "unknown_ouis": list(self.unknown_ouis),
            "total_known_co2": len(self.detected_ouis),
            "total_unknown": len(self.unknown_ouis)
        }
    
    def suggest_new_oui(self, device: BLEDevice, advertisement_data: AdvertisementData) -> Optional[Dict]:
        """新しいCO2デバイスOUIの提案"""
        analysis = self.analyze_device_by_oui(device, advertisement_data)
        
        # 既知・除外済みは提案しない
        if analysis["is_known_co2"] or analysis["is_excluded"]:
            return None
        
        # CO2関連の可能性をチェック
        suggestions = []
        
        # デバイス名にCO2が含まれる
        if device.name and 'co2' in device.name.lower():
            suggestions.append("device_name_contains_co2")
        
        # 製造者データのパターン
        if hasattr(advertisement_data, 'manufacturer_data') and advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if len(data) >= 8:
                    # CO2らしいデータパターン
                    suggestions.append(f"manufacturer_data_pattern_{manufacturer_id}")
        
        if suggestions:
            return {
                "oui": analysis["oui"],
                "mac_address": device.address,
                "device_name": device.name,
                "suggestions": suggestions,
                "manufacturer_data_info": getattr(advertisement_data, 'manufacturer_data', {})
            }
        
        return None