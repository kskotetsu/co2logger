"""
Tests for sensor data models
"""
import pytest
from datetime import datetime, timezone
from co2logger.models.sensor_data import CO2SensorData, TemperatureData, HumidityData


class TestCO2SensorData:
    """Test cases for CO2SensorData model"""
    
    def test_create_co2_sensor_data_with_valid_values(self):
        """Test creating CO2SensorData with valid values"""
        timestamp = datetime.now(timezone.utc)
        data = CO2SensorData(
            timestamp=timestamp,
            co2_ppm=400,
            temperature=25.5,
            humidity=60.0,
            device_address="AA:BB:CC:DD:EE:FF",
            raw_data="010203"
        )
        
        assert data.timestamp == timestamp
        assert data.co2_ppm == 400
        assert data.temperature == 25.5
        assert data.humidity == 60.0
        assert data.device_address == "AA:BB:CC:DD:EE:FF"
        assert data.raw_data == "010203"
    
    def test_co2_sensor_data_with_negative_co2_raises_error(self):
        """Test that negative CO2 values raise ValueError"""
        with pytest.raises(ValueError, match="CO2 ppm cannot be negative"):
            CO2SensorData(
                timestamp=datetime.now(timezone.utc),
                co2_ppm=-10,
                temperature=25.5,
                humidity=60.0,
                device_address="AA:BB:CC:DD:EE:FF"
            )
    
    def test_co2_sensor_data_with_invalid_humidity_raises_error(self):
        """Test that invalid humidity values raise ValueError"""
        with pytest.raises(ValueError, match="Humidity must be between 0 and 100"):
            CO2SensorData(
                timestamp=datetime.now(timezone.utc),
                co2_ppm=400,
                temperature=25.5,
                humidity=150.0,
                device_address="AA:BB:CC:DD:EE:FF"
            )
    
    def test_co2_sensor_data_to_dict(self):
        """Test converting CO2SensorData to dictionary"""
        timestamp = datetime.now(timezone.utc)
        data = CO2SensorData(
            timestamp=timestamp,
            co2_ppm=400,
            temperature=25.5,
            humidity=60.0,
            device_address="AA:BB:CC:DD:EE:FF",
            raw_data="010203"
        )
        
        result = data.to_dict()
        expected = {
            "timestamp": timestamp.isoformat(),
            "co2_ppm": 400,
            "temperature": 25.5,
            "humidity": 60.0,
            "device_address": "AA:BB:CC:DD:EE:FF",
            "raw_data": "010203"
        }
        
        assert result == expected
    
    def test_co2_sensor_data_from_dict(self):
        """Test creating CO2SensorData from dictionary"""
        timestamp = datetime.now(timezone.utc)
        data_dict = {
            "timestamp": timestamp.isoformat(),
            "co2_ppm": 400,
            "temperature": 25.5,
            "humidity": 60.0,
            "device_address": "AA:BB:CC:DD:EE:FF",
            "raw_data": "010203"
        }
        
        data = CO2SensorData.from_dict(data_dict)
        
        assert data.timestamp == timestamp
        assert data.co2_ppm == 400
        assert data.temperature == 25.5
        assert data.humidity == 60.0
        assert data.device_address == "AA:BB:CC:DD:EE:FF"
        assert data.raw_data == "010203"
    
    def test_co2_sensor_data_equality(self):
        """Test CO2SensorData equality comparison"""
        timestamp = datetime.now(timezone.utc)
        data1 = CO2SensorData(
            timestamp=timestamp,
            co2_ppm=400,
            temperature=25.5,
            humidity=60.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
        data2 = CO2SensorData(
            timestamp=timestamp,
            co2_ppm=400,
            temperature=25.5,
            humidity=60.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
        
        assert data1 == data2
    
    def test_co2_sensor_data_string_representation(self):
        """Test CO2SensorData string representation"""
        timestamp = datetime.now(timezone.utc)
        data = CO2SensorData(
            timestamp=timestamp,
            co2_ppm=400,
            temperature=25.5,
            humidity=60.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
        
        str_repr = str(data)
        assert "400 ppm" in str_repr
        assert "25.5°C" in str_repr
        assert "60.0%" in str_repr
        assert "AA:BB:CC:DD:EE:FF" in str_repr


class TestTemperatureData:
    """Test cases for TemperatureData model"""
    
    def test_create_temperature_data(self):
        """Test creating TemperatureData"""
        timestamp = datetime.now(timezone.utc)
        data = TemperatureData(
            timestamp=timestamp,
            temperature=25.5,
            device_address="AA:BB:CC:DD:EE:FF"
        )
        
        assert data.timestamp == timestamp
        assert data.temperature == 25.5
        assert data.device_address == "AA:BB:CC:DD:EE:FF"
    
    def test_temperature_data_extreme_values(self):
        """Test TemperatureData with extreme values"""
        with pytest.raises(ValueError, match="Temperature out of reasonable range"):
            TemperatureData(
                timestamp=datetime.now(timezone.utc),
                temperature=-100.0,
                device_address="AA:BB:CC:DD:EE:FF"
            )


class TestHumidityData:
    """Test cases for HumidityData model"""
    
    def test_create_humidity_data(self):
        """Test creating HumidityData"""
        timestamp = datetime.now(timezone.utc)
        data = HumidityData(
            timestamp=timestamp,
            humidity=60.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
        
        assert data.timestamp == timestamp
        assert data.humidity == 60.0
        assert data.device_address == "AA:BB:CC:DD:EE:FF"
    
    def test_humidity_data_boundary_values(self):
        """Test HumidityData with boundary values"""
        timestamp = datetime.now(timezone.utc)
        
        # Test minimum valid value
        data_min = HumidityData(
            timestamp=timestamp,
            humidity=0.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
        assert data_min.humidity == 0.0
        
        # Test maximum valid value
        data_max = HumidityData(
            timestamp=timestamp,
            humidity=100.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
        assert data_max.humidity == 100.0