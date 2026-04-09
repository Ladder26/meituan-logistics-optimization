"""
库存优化模块
负责确定单城市的最优订货周期
"""

from models import calculate_city_total_storage_cost
from .route_optimizer import optimize_city_routes


def calculate_city_total_cost(city_code: str, T: int, verbose: bool = False) -> dict:
    """
    计算城市在给定订货周期下的日总成本
    
    参数:
        city_code: 城市代码
        T: 订货周期
        verbose: 是否打印详细信息
    
    返回:
        {
            'city_code': 城市代码,
            'T': 订货周期,
            'storage_cost': 日均仓储成本,
            'transport_cost': 日均运输成本,
            'total_cost': 日总成本,
            'route_plan': 路径优化详情,
            'feasible': 是否可行
        }
    """
    # 1. 计算仓储成本
    storage_cost = calculate_city_total_storage_cost(city_code, T)
    
    # 2. 计算运输成本（通过路径优化）
    route_result = optimize_city_routes(city_code, T, verbose=verbose)
    
    if not route_result['feasible']:
        return {
            'city_code': city_code,
            'T': T,
            'storage_cost': storage_cost,
            'transport_cost': float('inf'),
            'total_cost': float('inf'),
            'route_plan': route_result,
            'feasible': False
        }
    
    transport_cost = route_result['daily_transport_cost']
    total_cost = storage_cost + transport_cost
    
    return {
        'city_code': city_code,
        'T': T,
        'storage_cost': storage_cost,
        'transport_cost': transport_cost,
        'total_cost': total_cost,
        'route_plan': route_result,
        'feasible': True
    }


def optimize_city_inventory(city_code: str, verbose: bool = False) -> dict:
    """
    寻找单城市的最优订货周期
    
    遍历 T=1 到 7，计算每个周期下的总成本，返回最优解
    
    参数:
        city_code: 城市代码
        verbose: 是否打印详细信息
    
    返回:
        {
            'city_code': 城市代码,
            'optimal_T': 最优订货周期,
            'optimal_cost': 最优日总成本,
            'storage_cost': 仓储成本,
            'transport_cost': 运输成本,
            'route_plan': 最优路径方案,
            'all_results': [T=1到7的所有结果],
            'cost_breakdown': 成本明细
        }
    """
    all_results = []
    best_result = None
    best_cost = float('inf')
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"City {city_code} 库存优化分析")
        print(f"{'='*70}")
        print(f"\n{'T(天)':<8} {'仓储成本':<15} {'运输成本':<15} {'总成本':<15} {'车辆数':<8}")
        print("-" * 70)
    
    for T in range(1, 8):
        result = calculate_city_total_cost(city_code, T, verbose=False)
        all_results.append(result)
        
        if result['feasible'] and result['total_cost'] < best_cost:
            best_cost = result['total_cost']
            best_result = result
        
        if verbose:
            n_vehicles = result['route_plan']['n_vehicles'] if result['feasible'] else '-'
            cost_str = f"{result['total_cost']:,.1f}" if result['feasible'] else '不可行'
            print(f"{T:<8} {result['storage_cost']:<15,.1f} {result['transport_cost']:<15,.1f} "
                  f"{cost_str:<15} {n_vehicles}")
    
    if best_result is None:
        raise ValueError(f"City {city_code}: 没有找到可行解")
    
    if verbose:
        print(f"\n✅ 最优方案: T={best_result['T']}天, 日总成本={best_result['total_cost']:,.1f}元")
        # 打印最优方案的路径详情
        optimize_city_routes(city_code, best_result['T'], verbose=True)
    
    return {
        'city_code': city_code,
        'optimal_T': best_result['T'],
        'optimal_cost': best_result['total_cost'],
        'storage_cost': best_result['storage_cost'],
        'transport_cost': best_result['transport_cost'],
        'route_plan': best_result['route_plan'],
        'all_results': all_results,
        'cost_breakdown': {
            'storage': best_result['storage_cost'],
            'transport': best_result['transport_cost'],
            'total': best_result['total_cost']
        }
    }


def analyze_cost_trend(city_code: str) -> dict:
    """
    分析城市在不同订货周期下的成本趋势
    
    返回用于可视化的数据
    
    参数:
        city_code: 城市代码
    
    返回:
        {
            'T_values': [1, 2, 3, 4, 5, 6, 7],
            'storage_costs': [...],
            'transport_costs': [...],
            'total_costs': [...]
        }
    """
    T_values = list(range(1, 8))
    storage_costs = []
    transport_costs = []
    total_costs = []
    
    for T in T_values:
        result = calculate_city_total_cost(city_code, T)
        storage_costs.append(result['storage_cost'])
        transport_costs.append(result['transport_cost'])
        total_costs.append(result['total_cost'])
    
    return {
        'city_code': city_code,
        'T_values': T_values,
        'storage_costs': storage_costs,
        'transport_costs': transport_costs,
        'total_costs': total_costs
    }


def print_inventory_analysis(result: dict):
    """打印库存优化分析结果"""
    city = result['city_code']
    
    print(f"\n{'='*70}")
    print(f"City {city} 库存优化报告")
    print(f"{'='*70}")
    
    print(f"\n【成本对比表】")
    print(f"{'T(天)':<8} {'仓储成本':<15} {'运输成本':<15} {'总成本':<15}")
    print("-" * 60)
    
    for r in result['all_results']:
        marker = " ← 最优" if r['T'] == result['optimal_T'] else ""
        print(f"{r['T']:<8} {r['storage_cost']:<15,.1f} {r['transport_cost']:<15,.1f} "
              f"{r['total_cost']:<15,.1f}{marker}")
    
    print(f"\n【最优方案详情】")
    print(f"  订货周期 T: {result['optimal_T']} 天")
    print(f"  日均仓储成本: {result['storage_cost']:,.1f} 元")
    print(f"  日均运输成本: {result['transport_cost']:,.1f} 元")
    print(f"  日总成本: {result['optimal_cost']:,.1f} 元")
    print(f"{'='*70}\n")
