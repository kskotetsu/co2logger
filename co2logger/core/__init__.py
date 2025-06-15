"""
Core package for CO2 logger Bluetooth communication
"""
from .bluetooth_device import BluetoothDeviceBase, DeviceScanner

__all__ = ["BluetoothDeviceBase", "DeviceScanner"]