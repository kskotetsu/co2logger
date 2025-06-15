"""
Sensor data models for CO2 logging
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SensorDataBase:
    """Base class for all sensor data"""
    timestamp: datetime
    device_address: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = {
            "timestamp": self.timestamp.isoformat(),
            "device_address": self.device_address,
        }
        if hasattr(self, 'raw_data') and self.raw_data is not None:
            result["raw_data"] = self.raw_data
        return result
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary"""
        data_copy = data.copy()
        if "timestamp" in data_copy:
            data_copy["timestamp"] = datetime.fromisoformat(data_copy["timestamp"])
        return cls(**data_copy)


@dataclass
class TemperatureData(SensorDataBase):
    """Temperature sensor data"""
    temperature: float
    raw_data: Optional[str] = None
    
    def __post_init__(self):
        """Validate temperature data after initialization"""
        if self.temperature < -50.0 or self.temperature > 100.0:
            raise ValueError("Temperature out of reasonable range (-50°C to 100°C)")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        result["temperature"] = self.temperature
        return result
    
    def __str__(self) -> str:
        return f"Temperature: {self.temperature}°C at {self.timestamp.strftime('%H:%M:%S')} ({self.device_address})"


@dataclass
class HumidityData(SensorDataBase):
    """Humidity sensor data"""
    humidity: float
    raw_data: Optional[str] = None
    
    def __post_init__(self):
        """Validate humidity data after initialization"""
        if self.humidity < 0.0 or self.humidity > 100.0:
            raise ValueError("Humidity must be between 0 and 100")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        result["humidity"] = self.humidity
        return result
    
    def __str__(self) -> str:
        return f"Humidity: {self.humidity}% at {self.timestamp.strftime('%H:%M:%S')} ({self.device_address})"


@dataclass
class CO2SensorData(SensorDataBase):
    """CO2 sensor data with temperature and humidity"""
    co2_ppm: int
    temperature: float
    humidity: float
    raw_data: Optional[str] = None
    
    def __post_init__(self):
        """Validate CO2 sensor data after initialization"""
        if self.co2_ppm < 0:
            raise ValueError("CO2 ppm cannot be negative")
        if self.humidity < 0.0 or self.humidity > 100.0:
            raise ValueError("Humidity must be between 0 and 100")
        if self.temperature < -50.0 or self.temperature > 100.0:
            raise ValueError("Temperature out of reasonable range (-50°C to 100°C)")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        result.update({
            "co2_ppm": self.co2_ppm,
            "temperature": self.temperature,
            "humidity": self.humidity
        })
        return result
    
    def __str__(self) -> str:
        return (f"CO2: {self.co2_ppm} ppm, Temp: {self.temperature}°C, "
                f"Humidity: {self.humidity}% at {self.timestamp.strftime('%H:%M:%S')} "
                f"({self.device_address})")
    
    def __eq__(self, other) -> bool:
        """Compare CO2SensorData instances"""
        if not isinstance(other, CO2SensorData):
            return False
        return (
            self.timestamp == other.timestamp and
            self.co2_ppm == other.co2_ppm and
            self.temperature == other.temperature and
            self.humidity == other.humidity and
            self.device_address == other.device_address and
            self.raw_data == other.raw_data
        )