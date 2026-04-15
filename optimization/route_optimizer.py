"""
路径优化模块
负责站点分组和车辆调度优化
"""

from itertools import combinations
from config import (
    get_daily_demand,
    get_city_parameters,
    get_vehicle_type,
    get_station_count,
    MAX_STATIONS_PER_TRIP,
)


def generate_all_groupings(n_stations: int, max_group_size: int = 3):
    """
    生成所有可能的站点分组方案（集合划分）
    
    使用回溯法生成所有将 n_stations 个站点划分为若干组（每组≤max_group_size）的方案
    
    参数:
        n_stations: 站点数量
        max_group_size: 每组最大站点数
    
    返回:
        分组方案列表，每个方案是一个列表的列表，如 [[0,1], [2,3], [4]]
    
    示例:
        >>> list(generate_all_groupings(3))
        [[[0], [1], [2]], [[0, 1], [2]], [[0, 2], [1]], [[0], [1, 2]], [[0, 1, 2]]]
    """
    stations = list(range(n_stations))
    
    def backtrack(remaining, current_groups):
        if not remaining:
            yield current_groups[:]
            return
        
        # 取第一个剩余站点作为新组的起点
        first = remaining[0]
        rest = remaining[1:]
        
        # 尝试将first加入现有组（如果组未满）
        for i, group in enumerate(current_groups):
            if len(group) < max_group_size:
                current_groups[i] = group + [first]
                yield from backtrack(rest, current_groups)
                current_groups[i] = group  # 回溯
        
        # 尝试将first作为新组的起点
        current_groups.append([first])
        yield from backtrack(rest, current_groups)
        current_groups.pop()  # 回溯
    
    yield from backtrack(stations, [])


def calculate_vehicle_plan(city_code: str, station_indices: list, T: int) -> dict:
    """
    为一组站点计算最优车辆配置方案（支持多车配送）

    返回中增加每辆车的站点访问顺序和装载变化
    """
    # 计算总需求
    total_demand = sum(get_daily_demand(city_code, i) * T for i in station_indices)

    # 获取车辆参数
    small = get_vehicle_type('small')
    large = get_vehicle_type('large')

    city_params = get_city_parameters(city_code)
    k = len(station_indices)

    # 计算该分组的里程
    distance = calculate_group_distance(city_params['cdc_distance'],
                                        city_params['inter_station_distance'], k)

    # 计算各站点的单次配送需求量（按T天计算）
    station_demands = []
    for i in station_indices:
        daily = get_daily_demand(city_code, i)
        station_demands.append({
            'station_index': i,
            'station_name': f"{city_code}_{i + 1}",
            'daily_demand': daily,
            'order_quantity': daily * T  # 单次配送量
        })

    # 按站点索引排序（确定访问顺序）
    station_demands.sort(key=lambda x: x['station_index'])

    # 尝试所有可能的车辆组合，找成本最低的
    max_vehicles = (total_demand + small['capacity'] - 1) // small['capacity']
    max_vehicles = min(max_vehicles, 10)

    best_plan = None
    best_cost = float('inf')

    # 枚举小车数量，其余用大车
    for n_small in range(max_vehicles + 1):
        n_large = 0
        capacity = n_small * small['capacity']

        remaining = total_demand - capacity
        if remaining > 0:
            n_large = (remaining + large['capacity'] - 1) // large['capacity']
            capacity += n_large * large['capacity']

        if capacity < total_demand:
            continue

        # 计算该配置的成本
        small_cost = small['fixed_cost'] + small['variable_cost'] * distance
        large_cost = large['fixed_cost'] + large['variable_cost'] * distance

        total_cost = n_small * small_cost + n_large * large_cost

        if total_cost < best_cost:
            best_cost = total_cost

            # 构建详细的车辆分配方案（包含装载变化）
            vehicles_detail = []
            remaining_demands = [s['order_quantity'] for s in station_demands]

            # 分配小车
            for v_idx in range(n_small):
                vehicle_load_detail = []
                current_load = 0

                # 按顺序装货（确定每站装多少）
                for s_idx, s in enumerate(station_demands):
                    if remaining_demands[s_idx] > 0:
                        # 能装多少装多少
                        can_load = min(remaining_demands[s_idx], small['capacity'] - current_load)
                        if can_load > 0:
                            vehicle_load_detail.append({
                                'station_name': s['station_name'],
                                'station_index': s['station_index'],
                                'load_amount': can_load,
                                'load_after_stop': current_load + can_load  # 装货后装载量
                            })
                            current_load += can_load
                            remaining_demands[s_idx] -= can_load

                        if current_load >= small['capacity']:
                            break

                # 计算到达每个站点时的装载率（卸货前/装货后）
                route_stops = []
                remaining_load = current_load
                for stop in vehicle_load_detail:
                    route_stops.append({
                        'station_name': stop['station_name'],
                        'action': '卸货',
                        'unload_amount': stop['load_amount'],
                        'load_before_unload': remaining_load,  # 卸货前装载量
                        'load_after_unload': remaining_load - stop['load_amount'],  # 卸货后装载量
                        'load_rate_before': remaining_load / small['capacity'] * 100,
                        'load_rate_after': (remaining_load - stop['load_amount']) / small['capacity'] * 100
                    })
                    remaining_load -= stop['load_amount']

                vehicles_detail.append({
                    'vehicle_id': f"S-{v_idx + 1}",
                    'type': 'small',
                    'capacity': small['capacity'],
                    'total_load': current_load,
                    'load_rate': current_load / small['capacity'] * 100,
                    'route_stops': route_stops,
                    'n_stops': len(route_stops)
                })

            # 分配大车
            for v_idx in range(n_large):
                vehicle_load_detail = []
                current_load = 0

                for s_idx, s in enumerate(station_demands):
                    if remaining_demands[s_idx] > 0:
                        can_load = min(remaining_demands[s_idx], large['capacity'] - current_load)
                        if can_load > 0:
                            vehicle_load_detail.append({
                                'station_name': s['station_name'],
                                'station_index': s['station_index'],
                                'load_amount': can_load,
                                'load_after_stop': current_load + can_load
                            })
                            current_load += can_load
                            remaining_demands[s_idx] -= can_load

                        if current_load >= large['capacity']:
                            break

                # 计算到达每个站点时的装载率
                route_stops = []
                remaining_load = current_load
                for stop in vehicle_load_detail:
                    route_stops.append({
                        'station_name': stop['station_name'],
                        'action': '卸货',
                        'unload_amount': stop['load_amount'],
                        'load_before_unload': remaining_load,
                        'load_after_unload': remaining_load - stop['load_amount'],
                        'load_rate_before': remaining_load / large['capacity'] * 100,
                        'load_rate_after': (remaining_load - stop['load_amount']) / large['capacity'] * 100
                    })
                    remaining_load -= stop['load_amount']

                vehicles_detail.append({
                    'vehicle_id': f"L-{v_idx + 1}",
                    'type': 'large',
                    'capacity': large['capacity'],
                    'total_load': current_load,
                    'load_rate': current_load / large['capacity'] * 100,
                    'route_stops': route_stops,
                    'n_stops': len(route_stops)
                })

            best_plan = {
                'vehicles': vehicles_detail,
                'n_small': n_small,
                'n_large': n_large,
                'total_trip_cost': total_cost,
                'total_capacity': capacity,
                'total_demand': total_demand,
                'distance': distance,
                'station_demands': station_demands,  # 各站点需求明细
                'feasible': True
            }

    if best_plan is None:
        return {
            'vehicles': [],
            'n_small': 0,
            'n_large': 0,
            'total_trip_cost': float('inf'),
            'total_capacity': 0,
            'total_demand': total_demand,
            'feasible': False
        }

    return best_plan


def calculate_group_distance(cdc_distance: float, inter_station_distance: float, k: int) -> float:
    """
    计算配送一组站点的总里程
    
    参数:
        cdc_distance: CDC到城市的距离
        inter_station_distance: 站点间距离
        k: 站点数
    
    返回:
        总里程
    """
    return 2 * cdc_distance + (k - 1) * inter_station_distance


def calculate_group_transport_cost(city_code: str, station_indices: list, T: int) -> dict:
    """
    计算一组站点的运输成本（外部接口，保持兼容）
    
    参数:
        city_code: 城市代码
        station_indices: 站点索引列表
        T: 订货周期
    
    返回:
        {
            'single_trip_cost': 单次配送成本,
            'daily_transport_cost': 日均运输成本,
            'vehicle_plan': 车辆配置详情
        }
    """
    plan = calculate_vehicle_plan(city_code, station_indices, T)
    
    return {
        'single_trip_cost': plan['total_trip_cost'],
        'daily_transport_cost': plan['total_trip_cost'] / T,
        'vehicle_plan': plan
    }


def optimize_city_routes(city_code: str, T: int, verbose: bool = False) -> dict:
    """
    优化城市的站点分组和车辆调度方案
    
    遍历所有可能的分组方案，选择总成本最低的
    
    参数:
        city_code: 城市代码
        T: 订货周期
        verbose: 是否打印详细信息
    
    返回:
        {
            'city_code': 城市代码,
            'T': 订货周期,
            'grouping_plan': 最优分组方案,
            'vehicle_plans': 每组车辆配置,
            'single_trip_cost': 单次配送总成本,
            'daily_transport_cost': 日均运输成本,
            'n_vehicles': 总车辆数,
            'feasible': 是否可行
        }
    """
    n_stations = get_station_count(city_code)
    
    best_solution = None
    best_cost = float('inf')
    
    # 遍历所有分组方案
    for grouping in generate_all_groupings(n_stations, MAX_STATIONS_PER_TRIP):
        total_trip_cost = 0
        vehicle_plans = []
        feasible = True
        
        for group in grouping:
            plan = calculate_vehicle_plan(city_code, group, T)
            
            if not plan['feasible']:
                feasible = False
                break
            
            total_trip_cost += plan['total_trip_cost']
            vehicle_plans.append({
                'group': group,
                'plan': plan
            })
        
        if not feasible:
            continue
        
        # 更新最优解
        if total_trip_cost < best_cost:
            best_cost = total_trip_cost
            best_solution = {
                'city_code': city_code,
                'T': T,
                'grouping_plan': grouping,
                'vehicle_plans': vehicle_plans,
                'single_trip_cost': total_trip_cost,
                'daily_transport_cost': total_trip_cost / T,
                'n_vehicles': sum(p['plan']['n_small'] + p['plan']['n_large'] for p in vehicle_plans),
                'feasible': True
            }
    
    if best_solution is None:
        return {
            'city_code': city_code,
            'T': T,
            'grouping_plan': [],
            'vehicle_plans': [],
            'single_trip_cost': float('inf'),
            'daily_transport_cost': float('inf'),
            'n_vehicles': 0,
            'feasible': False
        }
    
    if verbose:
        print_route_plan(best_solution)
    
    return best_solution


def print_route_plan(solution: dict):
    """打印路径优化结果"""
    city = solution['city_code']
    T = solution['T']
    
    print(f"\n{'='*70}")
    print(f"City {city} 路径优化结果 (T={T}天)")
    print(f"{'='*70}")
    
    print(f"\n分组方案:")
    for i, vp in enumerate(solution['vehicle_plans']):
        group = vp['group']
        plan = vp['plan']
        stations_str = ', '.join([f"{city}_{s+1}" for s in group])
        
        print(f"  第{i+1}组: 站点 [{stations_str}]")
        print(f"    总需求: {plan['total_demand']:,} pcs")
        print(f"    配送里程: {plan['distance']} km")
        print(f"    车辆配置: 小车×{plan['n_small']} + 大车×{plan['n_large']}")
        print(f"    单次配送成本: {plan['total_trip_cost']:,.1f} 元")
    
    print(f"\n成本汇总:")
    print(f"  单次配送总成本: {solution['single_trip_cost']:,.1f} 元")
    print(f"  日均运输成本: {solution['daily_transport_cost']:,.1f} 元")
    print(f"  总车辆数: {solution['n_vehicles']} 辆")
    print(f"{'='*70}\n")


def quick_route_plan(city_code: str, T: int) -> list:
    """
    快速生成一个合理的分组方案（非最优，用于测试）
    
    策略：贪心算法，按需求排序，尽量填满每辆车
    
    参数:
        city_code: 城市代码
        T: 订货周期
    
    返回:
        分组方案，如 [[0,1], [2,3], [4,5]]
    """
    n_stations = get_station_count(city_code)
    stations = list(range(n_stations))
    
    # 按需求排序（降序）
    stations.sort(key=lambda i: get_daily_demand(city_code, i), reverse=True)
    
    groups = []
    current_group = []
    current_demand = 0
    large = get_vehicle_type('large')
    
    for s in stations:
        demand = get_daily_demand(city_code, s) * T
        
        # 检查加入当前组是否会超载
        if len(current_group) < MAX_STATIONS_PER_TRIP and current_demand + demand <= large['capacity']:
            current_group.append(s)
            current_demand += demand
        else:
            # 开启新组
            if current_group:
                groups.append(current_group)
            current_group = [s]
            current_demand = demand
    
    if current_group:
        groups.append(current_group)
    
    return groups
