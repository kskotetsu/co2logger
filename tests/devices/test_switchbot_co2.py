"""
SwitchBot CO2センサー専用クラスのテスト
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from co2logger.devices.switchbot_co2 import SwitchBotCO2Sensor
from co2logger.models.sensor_data import CO2SensorData


class TestSwitchBotCO2Sensor:
    """SwitchBot CO2センサークラスのテストケース"""
    
    @pytest.fixture
    def mock_ble_device(self):
        """モックBLEデバイスを作成"""
        device = MagicMock(spec=BLEDevice)
        device.name = "SwitchBot Meter Pro CO2"
        device.address = "AA:BB:CC:DD:EE:FF"
        return device
    
    @pytest.fixture
    def co2_sensor(self, mock_ble_device):
        """CO2センサーインスタンスを作成"""
        return SwitchBotCO2Sensor(mock_ble_device)
    
    def test_co2_sensor_initialization(self, mock_ble_device):
        """CO2センサーの初期化をテスト"""
        sensor = SwitchBotCO2Sensor(mock_ble_device)
        
        assert sensor.ble_device == mock_ble_device
        assert sensor.device_type == 0x7B  # CO2センサーのデバイスタイプ
        assert sensor.latest_data is None
        assert sensor.data_callback is None
    
    def test_device_type_property(self, co2_sensor):
        """デバイスタイプのプロパティをテスト"""
        assert co2_sensor.device_type == 0x7B
    
    def test_is_co2_sensor_class_method_valid_device(self):
        """有効なCO2センサーデバイスの判定をテスト"""
        device = MagicMock(spec=BLEDevice)
        device.name = "SwitchBot Meter Pro CO2"
        
        mock_ad_data = MagicMock()
        mock_ad_data.service_data = {"fee7": b'\x7b\x01\x02\x03\x04'}  # 0x7b = CO2センサー
        
        assert SwitchBotCO2Sensor.is_co2_sensor(device, mock_ad_data) is True
    
    def test_is_co2_sensor_class_method_invalid_device(self):
        """無効なデバイスの判定をテスト"""
        device = MagicMock(spec=BLEDevice)
        device.name = "Other Device"
        
        mock_ad_data = MagicMock()
        mock_ad_data.service_data = {"fee7": b'\x73\x01\x02\x03\x04'}  # 0x73 = 温湿度計
        
        assert SwitchBotCO2Sensor.is_co2_sensor(device, mock_ad_data) is False
    
    def test_is_co2_sensor_by_name_only(self):
        """デバイス名のみでのCO2センサー判定をテスト"""
        device = MagicMock(spec=BLEDevice)
        device.name = "SwitchBot Meter Pro CO2"
        
        assert SwitchBotCO2Sensor.is_co2_sensor(device, None) is True
    
    def test_parse_advertisement_data_valid(self, co2_sensor):
        """有効なアドバタイズメントデータの解析をテスト"""
        ad_data = MagicMock()
        # CO2=400ppm (0x0190), temp=28℃, humidity=60%, device_type=0x7B
        ad_data.service_data = {
            "fee7": b'\x7b\x50\x90\x01\x1c\x3c\x00'  # リトルエンディアン: 0x0190 = 400
        }
        
        result = co2_sensor.parse_advertisement_data(ad_data)
        
        assert result is not None
        assert result["device_type"] == 0x7B
        assert result["co2_ppm"] == 400
        assert result["temperature"] == 28.0
        assert result["humidity"] == 60.0
        assert result["is_encrypted"] is False  # 0x7bのbit7が0
    
    def test_parse_advertisement_data_invalid(self, co2_sensor):
        """無効なアドバタイズメントデータの解析をテスト"""
        ad_data = MagicMock()
        ad_data.service_data = {"fee7": b'\x73\x01\x02'}  # 温湿度計のデータ
        
        result = co2_sensor.parse_advertisement_data(ad_data)
        
        assert result is None
    
    def test_parse_characteristic_data_valid(self, co2_sensor):
        """有効な特性データの解析をテスト"""
        # SwitchBotのCO2センサー応答データ
        # header[2] + status + battery + co2_ppm(little endian) + temp + humidity + reserved[2]
        char_data = b'\x57\x0b\x90\x50\x90\x01\x1c\x3c\x01\x02'  # CO2=400(0x0190), temp=28, humidity=60
        
        result = co2_sensor.parse_characteristic_data(char_data)
        
        assert isinstance(result, CO2SensorData)
        assert result.co2_ppm == 400
        assert result.temperature == 28.0
        assert result.humidity == 60.0
        assert result.device_address == "AA:BB:CC:DD:EE:FF"
    
    def test_parse_characteristic_data_invalid_length(self, co2_sensor):
        """長さが不正な特性データの解析をテスト"""
        char_data = b'\x57\x0b'  # データが短すぎる
        
        with pytest.raises(ValueError, match="データ長が不正"):
            co2_sensor.parse_characteristic_data(char_data)
    
    def test_parse_characteristic_data_invalid_header(self, co2_sensor):
        """ヘッダーが不正な特性データの解析をテスト"""
        char_data = b'\x00\x00\x90\x01\x64\x00\x3c\x28\x01\x02'  # 不正なヘッダー
        
        with pytest.raises(ValueError, match="CO2センサーデータではありません"):
            co2_sensor.parse_characteristic_data(char_data)
    
    @pytest.mark.asyncio
    async def test_request_sensor_data_success(self, co2_sensor):
        """センサーデータ要求の成功をテスト"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        co2_sensor.client = mock_client
        
        await co2_sensor.request_sensor_data()
        
        # CO2センサーデータ要求コマンドが送信されたことを確認
        mock_client.write_gatt_char.assert_called_once()
        call_args = mock_client.write_gatt_char.call_args
        assert call_args[0][0] == "cba20002-224d-11e6-9fb8-0002a5d5c51b"  # write特性UUID
        assert len(call_args[0][1]) > 0  # コマンドデータが送信された
    
    @pytest.mark.asyncio
    async def test_request_sensor_data_not_connected(self, co2_sensor):
        """接続されていない状態でのデータ要求をテスト"""
        with pytest.raises(RuntimeError, match="デバイスが接続されていません"):
            await co2_sensor.request_sensor_data()
    
    def test_set_data_callback(self, co2_sensor):
        """データコールバックの設定をテスト"""
        callback = MagicMock()
        co2_sensor.set_data_callback(callback)
        
        assert co2_sensor.data_callback == callback
    
    def test_notification_handler_valid_data(self, co2_sensor):
        """有効な通知データのハンドラーをテスト"""
        callback = MagicMock()
        co2_sensor.set_data_callback(callback)
        
        # 有効なCO2センサーデータ
        data = b'\x57\x0b\x90\x50\x90\x01\x1c\x3c\x01\x02'  # CO2=400, temp=28, humidity=60
        
        co2_sensor._notification_handler(None, data)
        
        # latest_dataが更新されたことを確認
        assert co2_sensor.latest_data is not None
        assert co2_sensor.latest_data.co2_ppm == 400
        
        # コールバックが呼ばれたことを確認
        callback.assert_called_once_with(co2_sensor.latest_data)
    
    def test_notification_handler_invalid_data(self, co2_sensor):
        """無効な通知データのハンドラーをテスト"""
        callback = MagicMock()
        co2_sensor.set_data_callback(callback)
        
        # 無効なデータ
        data = b'\x00\x00'
        
        co2_sensor._notification_handler(None, data)
        
        # latest_dataは更新されない
        assert co2_sensor.latest_data is None
        
        # コールバックは呼ばれない
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_start_monitoring_success(self, co2_sensor):
        """監視開始の成功をテスト"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.start_notify = AsyncMock()
        co2_sensor.client = mock_client
        
        await co2_sensor.start_monitoring()
        
        # 通知が開始されたことを確認
        mock_client.start_notify.assert_called_once_with(
            "cba20003-224d-11e6-9fb8-0002a5d5c51b",  # notify特性UUID
            co2_sensor._notification_handler
        )
    
    @pytest.mark.asyncio
    async def test_stop_monitoring_success(self, co2_sensor):
        """監視停止の成功をテスト"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.stop_notify = AsyncMock()
        co2_sensor.client = mock_client
        
        await co2_sensor.stop_monitoring()
        
        # 通知が停止されたことを確認
        mock_client.stop_notify.assert_called_once_with(
            "cba20003-224d-11e6-9fb8-0002a5d5c51b"  # notify特性UUID
        )
    
    @pytest.mark.asyncio
    async def test_get_current_data_with_request(self, co2_sensor):
        """データ要求付きの現在データ取得をテスト"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        co2_sensor.client = mock_client
        
        # データが返される前の状態をシミュレート
        co2_sensor.latest_data = None
        
        with patch('asyncio.sleep') as mock_sleep:
            # データ要求後にデータが設定されるようにシミュレート
            async def side_effect(*args):
                if not co2_sensor.latest_data:
                    # 最初のsleep後にデータを設定
                    test_data = CO2SensorData(
                        timestamp=datetime.now(timezone.utc),
                        co2_ppm=400,
                        temperature=25.0,
                        humidity=60.0,
                        device_address="AA:BB:CC:DD:EE:FF"
                    )
                    co2_sensor.latest_data = test_data
            
            mock_sleep.side_effect = side_effect
            
            result = await co2_sensor.get_current_data(request_new=True, timeout=2.0)
            
            assert result is not None
            assert result.co2_ppm == 400
            
            # データ要求が送信されたことを確認
            mock_client.write_gatt_char.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_current_data_timeout(self, co2_sensor):
        """データ取得のタイムアウトをテスト"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        co2_sensor.client = mock_client
        
        # データが設定されない状態
        co2_sensor.latest_data = None
        
        with patch('asyncio.sleep'):
            result = await co2_sensor.get_current_data(request_new=True, timeout=0.1)
            
            assert result is None
    
    def test_get_device_info(self, co2_sensor):
        """デバイス情報取得をテスト"""
        info = co2_sensor.get_device_info()
        
        expected = {
            "name": "SwitchBot Meter Pro CO2",
            "address": "AA:BB:CC:DD:EE:FF",
            "device_type": 0x7B,
            "device_type_name": "CO2センサー",
            "is_connected": False
        }
        
        assert info == expected