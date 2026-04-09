"""
全局搜索模块
负责遍历所有可能的订货周期组合，寻找全局最优解
"""

from itertools import product
from typing import List, Dict, Tuple
from config import CITIES
from .inventory_optimizer import calculate_city_total_cost


def generate_all_T_combinations() -> List[Tuple[int, ...]]:
    """
    生成所有可能的T组合
    
    5个城市，每个T∈{1,2,3,4,5,6,7}，共 7^5 = 16807 种组合
    
    返回:
        所有组合的列表，每个组合是一个元组 (T_A, T_B, T_C, T_D, T_E)
    """
    return list(product(range(1, 8), repeat=5))


def evaluate_T_combination(T_combo: Tuple[int, ...], verbose: bool = False) -> Dict:
    """
    评估一个T组合的总成本
    
    参数:
        T_combo: (T_A, T_B, T_C, T_D, T_E)
        verbose: 是否打印详细信息
    
    返回:
        {
            'T_combo': {'A': T_A, 'B': T_B, ...},
            'city_results': [每个城市的详细结果],
            'total_cost': 系统日总成本,
            'total_storage_cost': 总仓储成本,
            'total_transport_cost': 总运输成本,
            'feasible': 是否全部可行
        }
    """
    city_results = []
    total_cost = 0
    total_storage = 0
    total_transport = 0
    feasible = True
    
    T_dict = dict(zip(CITIES, T_combo))
    
    for city, T in zip(CITIES, T_combo):
        result = calculate_city_total_cost(city, T, verbose=False)
        city_results.append(result)
        
        if not result['feasible']:
            feasible = False
            total_cost = float('inf')
            break
        
        total_cost += result['total_cost']
        total_storage += result['storage_cost']
        total_transport += result['transport_cost']
    
    return {
        'T_combo': T_dict,
        'city_results': city_results,
        'total_cost': total_cost,
        'total_storage_cost': total_storage,
        'total_transport_cost': total_transport,
        'feasible': feasible
    }


def global_optimization(top_k: int = 10, verbose: bool = False) -> Dict:
    """
    全局优化：遍历所有T组合，寻找最优解
    
    参数:
        top_k: 返回前k个最优方案
        verbose: 是否打印进度信息
    
    返回:
        {
            'optimal_solution': 最优方案详情,
            'top_solutions': 前k个最优方案列表,
            'total_combinations': 总组合数,
            'evaluated_combinations': 评估的组合数
        }
    """
    all_combinations = generate_all_T_combinations()
    total = len(all_combinations)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"全局优化搜索")
        print(f"{'='*70}")
        print(f"总组合数: {total:,} (7^5 = 16,807)")
        print(f"正在评估...")
    
    # 存储所有可行解
    feasible_solutions = []
    
    for i, T_combo in enumerate(all_combinations):
        if verbose and (i + 1) % 2000 == 0:
            print(f"  进度: {i + 1}/{total} ({(i+1)/total*100:.1f}%)")
        
        result = evaluate_T_combination(T_combo)
        
        if result['feasible']:
            feasible_solutions.append(result)
    
    # 按总成本排序
    feasible_solutions.sort(key=lambda x: x['total_cost'])
    
    if not feasible_solutions:
        raise ValueError("没有找到可行解！")
    
    optimal = feasible_solutions[0]
    top_solutions = feasible_solutions[:top_k]
    
    if verbose:
        print(f"\n✅ 搜索完成!")
        print(f"   可行解数量: {len(feasible_solutions)}/{total}")
        print(f"   最优日总成本: {optimal['total_cost']:,.1f} 元")
        print_global_result(optimal, top_solutions)
    
    return {
        'optimal_solution': optimal,
        'top_solutions': top_solutions,
        'total_combinations': total,
        'evaluated_combinations': len(feasible_solutions)
    }


def print_global_result(optimal: Dict, top_solutions: List[Dict] = None):
    """打印全局优化结果"""
    print(f"\n{'='*70}")
    print(f"🎯 全局最优方案")
    print(f"{'='*70}")
    
    print(f"\n【各城市订货周期配置】")
    for city, T in optimal['T_combo'].items():
        city_result = next(r for r in optimal['city_results'] if r['city_code'] == city)
        print(f"  City {city}: T={T}天, "
              f"仓储={city_result['storage_cost']:,.0f}, "
              f"运输={city_result['transport_cost']:,.0f}, "
              f"小计={city_result['total_cost']:,.0f}")
    
    print(f"\n【成本汇总】")
    print(f"  系统日总成本: {optimal['total_cost']:,.1f} 元")
    print(f"    - 总仓储成本: {optimal['total_storage_cost']:,.1f} 元")
    print(f"    - 总运输成本: {optimal['total_transport_cost']:,.1f} 元")
    
    if top_solutions and len(top_solutions) > 1:
        print(f"\n【Top {len(top_solutions)} 方案对比】")
        print(f"{'排名':<6} {'A':<4} {'B':<4} {'C':<4} {'D':<4} {'E':<4} {'总成本':<15}")
        print("-" * 50)
        for i, sol in enumerate(top_solutions[:10], 1):
            T = sol['T_combo']
            marker = " ← 最优" if i == 1 else ""
            print(f"{i:<6} {T['A']:<4} {T['B']:<4} {T['C']:<4} {T['D']:<4} {T['E']:<4} "
                  f"{sol['total_cost']:<15,.1f}{marker}")
    
    print(f"{'='*70}\n")


def sensitivity_analysis(city_code: str = None) -> Dict:
    """
    敏感性分析：分析各城市T变化对总成本的影响
    
    参数:
        city_code: 如果指定，只分析该城市；否则分析所有城市
    
    返回:
        敏感性分析结果
    """
    from .inventory_optimizer import optimize_city_inventory
    
    cities_to_analyze = [city_code] if city_code else CITIES
    
    results = {}
    for city in cities_to_analyze:
        result = optimize_city_inventory(city)
        
        # 计算成本变化率
        all_costs = [r['total_cost'] for r in result['all_results']]
        min_cost = min(all_costs)
        max_cost = max(all_costs)
        
        results[city] = {
            'optimal_T': result['optimal_T'],
            'optimal_cost': result['optimal_cost'],
            'cost_range': (min_cost, max_cost),
            'cost_savings': (max_cost - min_cost) / max_cost * 100,  # 优化带来的节省百分比
            'all_results': result['all_results']
        }
    
    return results


def get_optimal_for_city(city_code: str) -> Dict:
    """
    获取单个城市的最优解（便捷接口）
    
    参数:
        city_code: 城市代码
    
    返回:
        城市最优解详情
    """
    from .inventory_optimizer import optimize_city_inventory
    return optimize_city_inventory(city_code, verbose=False)
