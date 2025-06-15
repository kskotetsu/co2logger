"""
Tests for Bluetooth device base classes
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from co2logger.core.bluetooth_device import BluetoothDeviceBase, DeviceScanner
from co2logger.models.sensor_data import CO2SensorData


class TestBluetoothDeviceBase:
    """Test cases for BluetoothDeviceBase"""
    
    @pytest.fixture
    def mock_ble_device(self):
        """Create a mock BLE device"""
        device = MagicMock(spec=BLEDevice)
        device.name = "SwitchBot Meter Pro CO2"
        device.address = "AA:BB:CC:DD:EE:FF"
        return device
    
    @pytest.fixture
    def bluetooth_device(self, mock_ble_device):
        """Create a BluetoothDeviceBase instance"""
        return BluetoothDeviceBase(mock_ble_device)
    
    def test_bluetooth_device_initialization(self, mock_ble_device):
        """Test BluetoothDeviceBase initialization"""
        device = BluetoothDeviceBase(mock_ble_device)
        
        assert device.ble_device == mock_ble_device
        assert device.client is None
        assert device.is_connected is False
        assert device.device_name == "SwitchBot Meter Pro CO2"
        assert device.device_address == "AA:BB:CC:DD:EE:FF"
    
    @pytest.mark.asyncio
    async def test_connect_success(self, bluetooth_device):
        """Test successful device connection"""
        with patch('co2logger.core.bluetooth_device.BleakClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.is_connected = True
            mock_client_class.return_value = mock_client
            
            result = await bluetooth_device.connect()
            
            assert result is True
            assert bluetooth_device.client == mock_client
            assert bluetooth_device.is_connected is True
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, bluetooth_device):
        """Test failed device connection"""
        with patch('co2logger.core.bluetooth_device.BleakClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client
            
            result = await bluetooth_device.connect()
            
            assert result is False
            assert bluetooth_device.client is None
            assert bluetooth_device.is_connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect_when_connected(self, bluetooth_device):
        """Test disconnecting from connected device"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        bluetooth_device.client = mock_client
        
        await bluetooth_device.disconnect()
        
        mock_client.disconnect.assert_called_once()
        assert bluetooth_device.client is None
        assert bluetooth_device.is_connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, bluetooth_device):
        """Test disconnecting when not connected"""
        await bluetooth_device.disconnect()
        
        assert bluetooth_device.client is None
        assert bluetooth_device.is_connected is False
    
    @pytest.mark.asyncio
    async def test_read_characteristic(self, bluetooth_device):
        """Test reading characteristic data"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.read_gatt_char.return_value = b'\x01\x02\x03'
        bluetooth_device.client = mock_client
        
        data = await bluetooth_device.read_characteristic("test-uuid")
        
        assert data == b'\x01\x02\x03'
        mock_client.read_gatt_char.assert_called_once_with("test-uuid")
    
    @pytest.mark.asyncio
    async def test_read_characteristic_not_connected(self, bluetooth_device):
        """Test reading characteristic when not connected"""
        with pytest.raises(RuntimeError, match="Device not connected"):
            await bluetooth_device.read_characteristic("test-uuid")
    
    @pytest.mark.asyncio
    async def test_write_characteristic(self, bluetooth_device):
        """Test writing characteristic data"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        bluetooth_device.client = mock_client
        
        await bluetooth_device.write_characteristic("test-uuid", b'\x01\x02\x03')
        
        mock_client.write_gatt_char.assert_called_once_with("test-uuid", b'\x01\x02\x03', response=True)
    
    @pytest.mark.asyncio
    async def test_start_notify(self, bluetooth_device):
        """Test starting notifications"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        bluetooth_device.client = mock_client
        
        callback = MagicMock()
        await bluetooth_device.start_notify("test-uuid", callback)
        
        mock_client.start_notify.assert_called_once_with("test-uuid", callback)
    
    @pytest.mark.asyncio
    async def test_stop_notify(self, bluetooth_device):
        """Test stopping notifications"""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        bluetooth_device.client = mock_client
        
        await bluetooth_device.stop_notify("test-uuid")
        
        mock_client.stop_notify.assert_called_once_with("test-uuid")


class TestDeviceScanner:
    """Test cases for DeviceScanner"""
    
    @pytest.fixture
    def scanner(self):
        """Create a DeviceScanner instance"""
        return DeviceScanner()
    
    @pytest.fixture
    def mock_ble_device(self):
        """Create a mock BLE device"""
        device = MagicMock(spec=BLEDevice)
        device.name = "SwitchBot Meter Pro CO2"
        device.address = "AA:BB:CC:DD:EE:FF"
        return device
    
    @pytest.fixture
    def mock_advertisement_data(self):
        """Create mock advertisement data"""
        ad_data = MagicMock(spec=AdvertisementData)
        ad_data.service_data = {
            "fee7": b'\x7b\x01\x02\x03\x04'  # 0x7b = 123 (CO2 sensor type)
        }
        return ad_data
    
    @pytest.mark.asyncio
    async def test_scan_for_devices(self, scanner):
        """Test device scanning"""
        mock_device = MagicMock(spec=BLEDevice)
        mock_device.name = "SwitchBot Device"
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        
        with patch('co2logger.core.bluetooth_device.BleakScanner') as mock_scanner_class:
            mock_scanner_class.discover = AsyncMock(return_value=[mock_device])
            
            devices = await scanner.scan_for_devices(scan_time=5)
            
            assert len(devices) == 1
            assert devices[0] == mock_device
            mock_scanner_class.discover.assert_called_once_with(timeout=5)
    
    def test_is_switchbot_device_by_name(self, scanner):
        """Test SwitchBot device identification by name"""
        device = MagicMock(spec=BLEDevice)
        device.name = "SwitchBot Meter Pro CO2"
        
        assert scanner.is_switchbot_device(device, None) is True
        
        device.name = "Other Device"
        assert scanner.is_switchbot_device(device, None) is False
        
        device.name = None
        assert scanner.is_switchbot_device(device, None) is False
    
    def test_is_switchbot_device_by_service_data(self, scanner):
        """Test SwitchBot device identification by service data"""
        device = MagicMock(spec=BLEDevice)
        device.name = "Unknown Device"
        
        # Create proper mock advertisement data
        mock_ad_data = MagicMock()
        mock_ad_data.service_data = {"fee7": b'\x7b\x01\x02\x03\x04'}
        
        # Test with valid SwitchBot service data
        assert scanner.is_switchbot_device(device, mock_ad_data) is True
        
        # Test with no service data
        mock_ad_data.service_data = {}
        assert scanner.is_switchbot_device(device, mock_ad_data) is False
        
        # Test with None advertisement data
        assert scanner.is_switchbot_device(device, None) is False
    
    @pytest.mark.asyncio
    async def test_scan_for_switchbot_devices(self, scanner):
        """Test scanning specifically for SwitchBot devices"""
        switchbot_device = MagicMock(spec=BLEDevice)
        switchbot_device.name = "SwitchBot Device"
        switchbot_device.address = "AA:BB:CC:DD:EE:FF"
        
        other_device = MagicMock(spec=BLEDevice)
        other_device.name = "Other Device"
        other_device.address = "11:22:33:44:55:66"
        
        with patch('co2logger.core.bluetooth_device.BleakScanner') as mock_scanner_class:
            mock_scanner_class.discover = AsyncMock(return_value=[switchbot_device, other_device])
            
            devices = await scanner.scan_for_switchbot_devices(scan_time=5)
            
            assert len(devices) == 1
            assert devices[0] == switchbot_device
    
    def test_detection_callback(self, scanner):
        """Test detection callback functionality"""
        detected_devices = []
        
        def callback(device, ad_data):
            detected_devices.append((device, ad_data))
        
        scanner.set_detection_callback(callback)
        
        # Create mock SwitchBot device
        mock_device = MagicMock(spec=BLEDevice)
        mock_device.name = "SwitchBot Device"
        
        mock_ad_data = MagicMock()
        mock_ad_data.service_data = {"fee7": b'\x7b\x01\x02\x03\x04'}
        
        # Test detection callback is called for SwitchBot devices
        result = scanner._detection_callback(mock_device, mock_ad_data)
        
        assert result is True
        assert len(detected_devices) == 1
        assert detected_devices[0] == (mock_device, mock_ad_data)
    
    def test_filter_devices_by_type(self, scanner):
        """Test filtering devices by type"""
        devices = [
            (MagicMock(name="Device 1"), {"device_type": 0x73}),  # Meter
            (MagicMock(name="Device 2"), {"device_type": 0x7b}),  # CO2 Meter
            (MagicMock(name="Device 3"), {"device_type": 0x48}),  # Bot
        ]
        
        co2_devices = scanner.filter_devices_by_type(devices, 0x7b)
        
        assert len(co2_devices) == 1
        assert co2_devices[0][1]["device_type"] == 0x7b