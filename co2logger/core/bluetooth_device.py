"""
Base classes for Bluetooth device communication
"""
import asyncio
import logging
from typing import Optional, List, Callable, Tuple, Dict, Any
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

logger = logging.getLogger(__name__)


class BluetoothDeviceBase:
    """Base class for Bluetooth device communication"""
    
    def __init__(self, ble_device: BLEDevice):
        """Initialize with BLE device"""
        self.ble_device = ble_device
        self.client: Optional[BleakClient] = None
        self._connection_timeout = 10.0
        
    @property
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.client is not None and self.client.is_connected
    
    @property
    def device_name(self) -> str:
        """Get device name"""
        return self.ble_device.name or "Unknown Device"
    
    @property
    def device_address(self) -> str:
        """Get device address"""
        return self.ble_device.address
    
    async def connect(self, timeout: Optional[float] = None) -> bool:
        """Connect to the device"""
        if self.is_connected:
            return True
            
        timeout = timeout or self._connection_timeout
        
        try:
            logger.info(f"Connecting to {self.device_name} ({self.device_address})")
            self.client = BleakClient(self.ble_device.address)
            await asyncio.wait_for(self.client.connect(), timeout=timeout)
            
            if self.client.is_connected:
                logger.info(f"Successfully connected to {self.device_name}")
                return True
            else:
                logger.error(f"Failed to connect to {self.device_name}")
                self.client = None
                return False
                
        except Exception as e:
            logger.error(f"Connection error for {self.device_name}: {e}")
            self.client = None
            return False
    
    async def disconnect(self):
        """Disconnect from the device"""
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
                logger.info(f"Disconnected from {self.device_name}")
            except Exception as e:
                logger.error(f"Disconnect error for {self.device_name}: {e}")
        
        self.client = None
    
    async def read_characteristic(self, characteristic_uuid: str) -> bytes:
        """Read data from a characteristic"""
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            data = await self.client.read_gatt_char(characteristic_uuid)
            logger.debug(f"Read {len(data)} bytes from {characteristic_uuid}")
            return data
        except Exception as e:
            logger.error(f"Read error from {characteristic_uuid}: {e}")
            raise
    
    async def write_characteristic(self, characteristic_uuid: str, data: bytes, response: bool = True):
        """Write data to a characteristic"""
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            await self.client.write_gatt_char(characteristic_uuid, data, response=response)
            logger.debug(f"Wrote {len(data)} bytes to {characteristic_uuid}")
        except Exception as e:
            logger.error(f"Write error to {characteristic_uuid}: {e}")
            raise
    
    async def start_notify(self, characteristic_uuid: str, callback: Callable):
        """Start notifications for a characteristic"""
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            await self.client.start_notify(characteristic_uuid, callback)
            logger.debug(f"Started notifications for {characteristic_uuid}")
        except Exception as e:
            logger.error(f"Notify start error for {characteristic_uuid}: {e}")
            raise
    
    async def stop_notify(self, characteristic_uuid: str):
        """Stop notifications for a characteristic"""
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            await self.client.stop_notify(characteristic_uuid)
            logger.debug(f"Stopped notifications for {characteristic_uuid}")
        except Exception as e:
            logger.error(f"Notify stop error for {characteristic_uuid}: {e}")
            raise


class DeviceScanner:
    """Scanner for Bluetooth devices"""
    
    def __init__(self):
        """Initialize scanner"""
        self._user_callback: Optional[Callable] = None
        self._discovered_devices: List[Tuple[BLEDevice, AdvertisementData]] = []
    
    def set_detection_callback(self, callback: Callable[[BLEDevice, AdvertisementData], None]):
        """Set callback for device detection"""
        self._user_callback = callback
    
    async def scan_for_devices(self, scan_time: float = 10.0) -> List[BLEDevice]:
        """Scan for all Bluetooth devices"""
        logger.info(f"Scanning for devices for {scan_time} seconds...")
        
        try:
            devices = await BleakScanner.discover(timeout=scan_time)
            logger.info(f"Found {len(devices)} devices")
            return devices
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return []
    
    async def scan_for_switchbot_devices(self, scan_time: float = 10.0) -> List[BLEDevice]:
        """Scan specifically for SwitchBot devices"""
        logger.info(f"Scanning for SwitchBot devices for {scan_time} seconds...")
        
        devices = await self.scan_for_devices(scan_time)
        switchbot_devices = []
        
        for device in devices:
            if self.is_switchbot_device(device, None):
                switchbot_devices.append(device)
                logger.info(f"Found SwitchBot device: {device.name} ({device.address})")
        
        return switchbot_devices
    
    def is_switchbot_device(self, device: BLEDevice, advertisement_data: Optional[AdvertisementData]) -> bool:
        """Check if device is a SwitchBot device"""
        # Check by device name
        if device.name and "switchbot" in device.name.lower():
            return True
        
        # Check by service data
        if advertisement_data and hasattr(advertisement_data, 'service_data') and advertisement_data.service_data:
            # SwitchBot devices advertise on service UUID "fee7"
            for uuid, data in advertisement_data.service_data.items():
                if isinstance(uuid, str) and uuid.lower() == "fee7" and len(data) > 0:
                    return True
        
        return False
    
    def _detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData) -> bool:
        """Internal detection callback"""
        if self.is_switchbot_device(device, advertisement_data):
            if self._user_callback:
                self._user_callback(device, advertisement_data)
            self._discovered_devices.append((device, advertisement_data))
            return True
        return False
    
    async def scan_with_callback(self, scan_time: float = 10.0) -> List[Tuple[BLEDevice, AdvertisementData]]:
        """Scan for devices using callback detection"""
        logger.info(f"Scanning with callback for {scan_time} seconds...")
        self._discovered_devices.clear()
        
        scanner = BleakScanner(detection_callback=self._detection_callback)
        await scanner.start()
        await asyncio.sleep(scan_time)
        await scanner.stop()
        
        logger.info(f"Found {len(self._discovered_devices)} SwitchBot devices via callback")
        return self._discovered_devices.copy()
    
    def filter_devices_by_type(self, devices: List[Tuple[BLEDevice, Dict[str, Any]]], device_type: int) -> List[Tuple[BLEDevice, Dict[str, Any]]]:
        """Filter devices by their device type"""
        filtered = []
        for device, data in devices:
            if data.get("device_type") == device_type:
                filtered.append((device, data))
        return filtered
    
    def parse_service_data(self, service_data: Dict[str, bytes]) -> Dict[str, Any]:
        """Parse SwitchBot service data"""
        parsed = {}
        
        for uuid, data in service_data.items():
            if uuid.lower() == "fee7" and len(data) > 0:
                # Parse SwitchBot service data format
                device_type = data[0] & 0x7F  # Lower 7 bits
                is_encrypted = (data[0] & 0x80) != 0  # Bit 7
                
                parsed.update({
                    "device_type": device_type,
                    "is_encrypted": is_encrypted,
                    "raw_service_data": data.hex()
                })
                
                # Parse additional data based on device type
                if len(data) > 1:
                    parsed["additional_data"] = data[1:].hex()
        
        return parsed