"""
成本计算模块
包含仓储成本和运输成本的计算函数
"""

from config import (
    get_daily_demand,
    get_city_parameters,
    get_vehicle_type,
    get_all_stations,
    STORAGE_CONVERSION,
    LEAD_TIME,
    MAX_STATIONS_PER_TRIP,
)


# ==================== 仓储成本计算 ====================

def calculate_peak_inventory(daily_demand: float, T: int) -> float:
    """
    计算某站点的峰值库存量
    
    参数:
        daily_demand: 日均销量 (pcs/天)
        T: 订货周期 (天)
    
    返回:
        峰值库存量 (pcs)
    
    公式:
        峰值库存 = 日均销量 × (订货周期 T + 提前期 2)
    """
    return daily_demand * (T + LEAD_TIME)


def calculate_required_area(peak_inventory: float) -> float:
    """
    计算所需仓库面积
    
    参数:
        peak_inventory: 峰值库存量 (pcs)
    
    返回:
        所需面积 (m²)
    
    公式:
        所需面积 = 峰值库存 / 1000 (pcs/m²)
    """
    return peak_inventory / STORAGE_CONVERSION


def calculate_daily_storage_cost(city_code: str, station_index: int, T: int) -> float:
    """
    计算某站点的日仓租
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
        station_index: 站点索引 (0-based)
        T: 订货周期 (天)
    
    返回:
        日仓租 (元/天)
    
    公式:
        日仓租 = 所需面积 × 单平方米租金
             = (日均销量 × (T + 2) / 1000) × rent_per_m2
    """
    # 获取数据
    daily_demand = get_daily_demand(city_code, station_index)
    city_params = get_city_parameters(city_code)
    rent_per_m2 = city_params['rent_per_m2']
    
    # 计算
    peak_inventory = calculate_peak_inventory(daily_demand, T)
    required_area = calculate_required_area(peak_inventory)
    daily_cost = required_area * rent_per_m2
    
    return daily_cost


def calculate_city_total_storage_cost(city_code: str, T: int) -> float:
    """
    计算某城市所有站点的总日仓租
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
        T: 订货周期 (天)
    
    返回:
        该城市所有站点的日仓租总和 (元/天)
    """
    stations = get_all_stations(city_code)
    total_cost = 0.0
    
    for i in range(len(stations)):
        station_cost = calculate_daily_storage_cost(city_code, i, T)
        total_cost += station_cost
    
    return total_cost


# ==================== 运输成本计算 ====================

def calculate_total_distance(city_code: str, k: int) -> float:
    """
    计算单次配送的总里程
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
        k: 服务站点数 (1-3)
    
    返回:
        总里程 (km)
    
    公式:
        总里程 = 2 × CDC 距离 + (k - 1) × 站点间距离
    
    说明:
        - 第一段：CDC → 第一个站点
        - 第二段：站点之间 (k-1) 段，每段 10km
        - 第三段：最后一个站点 → CDC（与第一段相同）
    """
    if k < 1 or k > MAX_STATIONS_PER_TRIP:
        raise ValueError(f"每车服务站点数必须在 1-{MAX_STATIONS_PER_TRIP} 之间，当前为{k}")
    
    city_params = get_city_parameters(city_code)
    cdc_distance = city_params['cdc_distance']
    inter_station_distance = city_params['inter_station_distance']
    
    # 总里程 = 2 × CDC 距离 + (k-1) × 站点间距离
    total_distance = 2 * cdc_distance + (k - 1) * inter_station_distance
    
    return total_distance


def calculate_single_trip_cost(city_code: str, k: int, vehicle_type: str) -> float:
    """
    计算单次配送的运输成本
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
        k: 服务站点数 (1-3)
        vehicle_type: 车型 ('large' 或 'small')
    
    返回:
        运输成本 (元)
    
    公式:
        运输成本 = 固定发车成本 + 变动成本 × 总里程
               = fixed_cost + variable_cost × total_distance
    """
    # 验证车型
    if vehicle_type not in ['large', 'small']:
        raise ValueError("车型必须是 'large' 或 'small'")
    
    # 计算总里程
    total_distance = calculate_total_distance(city_code, k)
    
    # 获取车型参数
    vehicle = get_vehicle_type(vehicle_type)
    fixed_cost = vehicle['fixed_cost']
    variable_cost_per_km = vehicle['variable_cost']
    
    # 计算总成本
    total_cost = fixed_cost + variable_cost_per_km * total_distance
    
    return total_cost


def check_capacity_constraint(station_demands: list, vehicle_type: str) -> bool:
    """
    检查载重约束：站点订货量之和是否小于等于车辆满载量
    
    参数:
        station_demands: 站点订货量列表 (pcs)
        vehicle_type: 车型 ('large' 或 'small')
    
    返回:
        True 如果满足约束，否则 False
    """
    vehicle = get_vehicle_type(vehicle_type)
    capacity = vehicle['capacity']
    total_demand = sum(station_demands)
    
    return total_demand <= capacity


def select_optimal_vehicle(city_code: str, station_indices: list, T: int = 1) -> str:
    """
    为一组站点选择最优车型

    策略:
        1. 优先使用小车（成本低）
        2. 如果超载则使用大车
        3. 如果大车也超载，返回 None（需要多辆车）

    参数:
        city_code: 城市代码
        station_indices: 站点索引列表
        T: 订货周期 (天)，单次运输量 = 日均销量 × T

    返回:
        最优车型 ('large' 或 'small')，如果都超载则返回 None
    """
    # 计算单次配送总需求 = 日均需求 × T
    demands = [get_daily_demand(city_code, i) * T for i in station_indices]
    total_demand = sum(demands)
    
    # 优先尝试小车
    small_vehicle = get_vehicle_type('small')
    if total_demand <= small_vehicle['capacity']:
        return 'small'
    
    # 尝试大车
    large_vehicle = get_vehicle_type('large')
    if total_demand <= large_vehicle['capacity']:
        return 'large'
    
    # 都超载
    return None


# ==================== 综合成本计算 ====================

def calculate_daily_total_cost(city_code: str, T: int, grouping_plan: list) -> float:
    """
    计算某城市在给定订货周期和分组方案下的日总成本
    
    参数:
        city_code: 城市代码 ('A', 'B', 'C', 'D', 'E')
        T: 订货周期 (天)
        grouping_plan: 分组方案，如 [[0,1,2], [3,4], [5]]
                      表示三辆车，第一辆服务站点 0,1,2；第二辆服务 3,4；第三辆服务 5
    
    返回:
        日总成本 (元/天) = 仓储成本 + 运输成本
    """
    # 1. 计算日均仓储成本
    storage_cost = calculate_city_total_storage_cost(city_code, T)

    # 2. 计算单次配送总运费
    single_delivery_cost = 0.0
    for group in grouping_plan:
        # 为每组选择最优车型（按 T 天的货量检查载重）
        vehicle_type = select_optimal_vehicle(city_code, group, T)
        if vehicle_type is None:
            station_names = [f"{city_code}_{i+1}" for i in group]
            raise ValueError(f"站点组{station_names}的单次订货量(日均×{T})超过最大车型载货量，需要拆分")

        # 计算该组的运输成本
        k = len(group)
        trip_cost = calculate_single_trip_cost(city_code, k, vehicle_type)
        single_delivery_cost += trip_cost

    # 3. 日均运输成本 = 单次配送总运费 / T
    daily_transport_cost = single_delivery_cost / T

    # 4. 日总成本 = 日均仓储成本 + 日均运输成本
    total_cost = storage_cost + daily_transport_cost
    
    return total_cost


# ==================== 辅助函数 ====================

def print_cost_breakdown(city_code: str, T: int, grouping_plan: list):
    """
    打印成本明细分解（用于调试和展示）
    
    参数:
        city_code: 城市代码
        T: 订货周期
        grouping_plan: 分组方案
    """
    print(f"\n{'='*60}")
    print(f"City {city_code} 成本明细 (T={T}天)")
    print(f"{'='*60}")
    
    # 仓储成本明细
    print(f"\n【仓储成本】")
    stations = get_all_stations(city_code)
    total_storage = 0
    for i, station in enumerate(stations):
        demand = get_daily_demand(city_code, i)
        peak = calculate_peak_inventory(demand, T)
        area = calculate_required_area(peak)
        rent = get_city_parameters(city_code)['rent_per_m2']
        cost = calculate_daily_storage_cost(city_code, i, T)
        total_storage += cost
        print(f"  {station}: 需求={demand:,} pcs → 峰值={peak:,} pcs → 面积={area:.1f} m² → 仓租={cost:.1f} 元/天")
    print(f"  仓储成本合计：{total_storage:,.1f} 元/天")
    
    # 运输成本明细
    print(f"\n【运输成本】(每 {T} 天配送一次)")
    total_transport = 0
    for idx, group in enumerate(grouping_plan):
        vehicle_type = select_optimal_vehicle(city_code, group, T)
        if vehicle_type is None:
            station_names = [stations[i] for i in group]
            demands_info = [f"{get_daily_demand(city_code, i)*T:,}" for i in group]
            print(f"  车辆{idx+1}: 服务{station_names} → 单次货量{demands_info} pcs → 超载！需要拆分")
            continue

        k = len(group)
        distance = calculate_total_distance(city_code, k)
        trip_cost = calculate_single_trip_cost(city_code, k, vehicle_type)
        total_transport += trip_cost

        station_names = [stations[i] for i in group]
        group_demand = sum(get_daily_demand(city_code, i) * T for i in group)
        vehicle_cap = get_vehicle_type(vehicle_type)['capacity']
        print(f"  车辆{idx+1}: 服务{station_names} → 货量={group_demand:,}/{vehicle_cap:,} pcs → 里程={distance} km → 车型={vehicle_type} → 单次成本={trip_cost:.1f} 元")

    daily_transport = total_transport / T
    print(f"  单次配送总运费：{total_transport:,.1f} 元")
    print(f"  日均运输成本：{total_transport:,.1f} / {T} = {daily_transport:,.1f} 元/天")
    
    # 总成本
    daily_transport = total_transport / T
    total_cost = total_storage + daily_transport
    print(f"\n【日总成本】")
    print(f"  日总成本 = 仓储 {total_storage:,.1f} + 运输 {daily_transport:,.1f} = {total_cost:,.1f} 元/天")
    print(f"{'='*60}\n")
