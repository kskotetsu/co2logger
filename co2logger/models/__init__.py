"""
Models package for CO2 logger
"""
from .sensor_data import CO2SensorData, TemperatureData, HumidityData, SensorDataBase

__all__ = ["CO2SensorData", "TemperatureData", "HumidityData", "SensorDataBase"]