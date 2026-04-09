"""
配置模块
提供所有固定参数、数据（城市/站点/车型）的访问接口
"""

from .parameters import (
    # 数据结构
    VEHICLE_TYPES,
    CITIES,
    STATIONS_PER_CITY,
    CITY_PARAMETERS,
    STATION_DEMANDS,
    
    # 约束条件
    MAX_STATIONS_PER_TRIP,
    LEAD_TIME,
    STORAGE_CONVERSION,
    
    # 辅助函数
    get_daily_demand,
    get_city_total_demand,
    get_station_count,
    get_city_parameters,
    get_vehicle_type,
    get_all_stations,
)

__all__ = [
    # 数据结构
    'VEHICLE_TYPES',
    'CITIES',
    'STATIONS_PER_CITY',
    'CITY_PARAMETERS',
    'STATION_DEMANDS',
    
    # 约束条件
    'MAX_STATIONS_PER_TRIP',
    'LEAD_TIME',
    'STORAGE_CONVERSION',
    
    # 辅助函数
    'get_daily_demand',
    'get_city_total_demand',
    'get_station_count',
    'get_city_parameters',
    'get_vehicle_type',
    'get_all_stations',
]
