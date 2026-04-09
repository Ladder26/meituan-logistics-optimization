# 车辆参数
VEHICLE_TYPES = {
    'large': {
        'fixed_cost': 600,      # 元/次
        'variable_cost': 6.5,   # 元/km
        'capacity': 200000      # pcs
    },
    # Type-l 车型
    'small': {
        'fixed_cost': 300,
        'variable_cost': 4.0,
        'capacity': 80000
    }
    # Type-S 车型
}

# 城市分布与仓储成本（CDC 距离 + 仓租 + 站点间固定距离）
CITY_PARAMETERS = {
    'A': {
        'cdc_distance': 40,       # CDC 到 City A 第一个站点的距离 (km)
        'rent_per_m2': 5.0,        # City A 的单平方米租金 (元/m²/天)
        'inter_station_distance': 10  # 站点间距离 (km)，选题为简化处理，统一设为10km
    },
    'B': {
        'cdc_distance': 70,
        'rent_per_m2': 4.0,
        'inter_station_distance': 10
    },
    'C': {
        'cdc_distance': 100,
        'rent_per_m2': 3.0,
        'inter_station_distance': 10
    },
    'D': {
        'cdc_distance': 140,
        'rent_per_m2': 2.0,
        'inter_station_distance': 10
    },
    'E': {
        'cdc_distance': 180,
        'rent_per_m2': 1.5,
        'inter_station_distance': 10
    }
}

# 站点需求数据
# 站点数
CITIES = ['A', 'B', 'C', 'D', 'E']
STATIONS_PER_CITY = {
    'A': 6,
    'B': 5,
    'C': 5,
    'D': 5,
    'E': 4
}

# 各站点日均销量 (万 PCS/天，已经转换为 pcs/天）
STATION_DEMANDS = {
    'A': [85000, 80000, 75000, 60000, 55000, 50000],      # City A: 6 个站点，高销量密集区
    'B': [60000, 55000, 50000, 45000, 40000],           # City B: 5 个站点，中高销量
    'C': [50000, 45000, 40000, 35000, 30000],           # City C: 5 个站点，中等销量
    'D': [35000, 30000, 25000, 20000, 15000],           # City D: 5 个站点，中低销量
    'E': [20000, 15000, 12000, 10000]                 # City E: 4 个站点，低销量，运距远
}

# 空间转化关系
STORAGE_CONVERSION = 1000  # 1000pcs / m²

# 约束条件
MAX_STATIONS_PER_TRIP = 3  # 每车最多服务 3 个站点
LEAD_TIME = 2  # 提前期（天）

# ==================== 辅助函数 ====================

def get_daily_demand(city_code, station_index):
    """
    获取指定城市指定站点的日均销量
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
        station_index: 站点索引 (0-based，如 0 表示第一个站点)
    
    返回:
        日均销量 (pcs/天)
    
    示例:
        >>> get_daily_demand('A', 0)  # City A 第 1 个站点
        85000
    """
    return STATION_DEMANDS[city_code][station_index]


def get_city_total_demand(city_code):
    """
    获取某城市的总日均销量
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
    
    返回:
        该城市所有站点的日均销量之和 (pcs/天)
    
    示例:
        >>> get_city_total_demand('A')  # City A 所有站点
        405000
    """
    return sum(STATION_DEMANDS[city_code])


def get_station_count(city_code):
    """
    获取某城市的站点数量
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
    
    返回:
        站点数量
    """
    return STATIONS_PER_CITY[city_code]


def get_city_parameters(city_code):
    """
    获取某城市的所有参数（距离、仓租等）
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
    
    返回:
        包含该城市所有参数的字典
    """
    return CITY_PARAMETERS[city_code]


def get_vehicle_type(vehicle_code):
    """
    获取指定车型的参数
    
    参数:
        vehicle_code: 车型代码 ('large' 或 'small')
    
    返回:
        包含该车型所有参数的字典
    """
    return VEHICLE_TYPES[vehicle_code]


def get_all_stations(city_code):
    """
    获取某城市的所有站点列表（带编号）
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
    
    返回:
        站点列表，如 ['A_1', 'A_2', ..., 'A_6']
    
    示例:
        >>> get_all_stations('A')
        ['A_1', 'A_2', 'A_3', 'A_4', 'A_5', 'A_6']
    """
    count = STATIONS_PER_CITY[city_code]
    return [f"{city_code}_{i+1}" for i in range(count)]
