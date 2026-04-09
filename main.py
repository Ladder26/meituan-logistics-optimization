#!/usr/bin/env python3
"""
美团物流优化系统 - 主程序入口

城市群零售网络物流与库存联合优化
"""

import json
from datetime import datetime
from pathlib import Path

from config import CITIES
from optimization import (
    optimize_city_inventory,
    global_optimization,
    optimize_city_routes,
)


def run_single_city_analysis(city_code: str, verbose: bool = True):
    """运行单城市分析"""
    if verbose:
        print(f"\n{'='*70}")
        print(f"City {city_code} 独立优化分析")
        print(f"{'='*70}")
    
    result = optimize_city_inventory(city_code, verbose=verbose)
    return result


def run_all_cities_analysis(verbose: bool = True):
    """运行所有城市独立优化分析"""
    if verbose:
        print(f"\n{'='*70}")
        print(f"各城市独立优化结果")
        print(f"{'='*70}")
        print(f"\n{'城市':<6} {'最优T':<8} {'仓储成本':<15} {'运输成本':<15} {'日总成本':<15}")
        print("-" * 70)
    
    results = {}
    total_cost = 0
    
    for city in CITIES:
        result = optimize_city_inventory(city, verbose=False)
        results[city] = result
        total_cost += result['optimal_cost']
        
        if verbose:
            print(f"{city:<6} {result['optimal_T']:<8} {result['storage_cost']:<15,.1f} "
                  f"{result['transport_cost']:<15,.1f} {result['optimal_cost']:<15,.1f}")
    
    if verbose:
        print(f"\n{'':<6} {'':<8} {'':<15} {'独立优化合计:':<15} {total_cost:<15,.1f}")
    
    return results, total_cost


def run_global_optimization(top_k: int = 10, verbose: bool = True):
    """运行全局优化"""
    result = global_optimization(top_k=top_k, verbose=verbose)
    return result


def generate_detailed_report(global_result: dict, output_dir: Path):
    """生成详细报告文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 保存全局最优方案 (JSON)
    optimal_file = output_dir / f"optimal_solution_{timestamp}.json"
    with open(optimal_file, 'w', encoding='utf-8') as f:
        json.dump(global_result['optimal_solution'], f, ensure_ascii=False, indent=2)
    
    # 2. 保存所有Top方案 (JSON)
    top_file = output_dir / f"top_solutions_{timestamp}.json"
    with open(top_file, 'w', encoding='utf-8') as f:
        json.dump(global_result['top_solutions'], f, ensure_ascii=False, indent=2)
    
    # 3. 生成文本报告
    report_file = output_dir / f"optimization_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("美团物流优化系统 - 优化报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        # 最优方案
        optimal = global_result['optimal_solution']
        f.write("【全局最优方案】\n\n")
        f.write(f"系统日总成本最小值: {optimal['total_cost']:,.2f} 元\n")
        f.write(f"  - 总仓储成本: {optimal['total_storage_cost']:,.2f} 元\n")
        f.write(f"  - 总运输成本: {optimal['total_transport_cost']:,.2f} 元\n\n")
        
        f.write("各城市配置:\n")
        for city, T in optimal['T_combo'].items():
            city_result = next(r for r in optimal['city_results'] if r['city_code'] == city)
            f.write(f"  City {city}: T={T}天\n")
            f.write(f"    仓储成本: {city_result['storage_cost']:,.2f} 元/天\n")
            f.write(f"    运输成本: {city_result['transport_cost']:,.2f} 元/天\n")
            f.write(f"    日总成本: {city_result['total_cost']:,.2f} 元/天\n")
            
            # 车辆调度详情
            route_plan = city_result['route_plan']
            f.write(f"    车辆调度:\n")
            for i, vp in enumerate(route_plan['vehicle_plans'], 1):
                group = vp['group']
                plan = vp['plan']
                stations_str = ', '.join([f"{city}_{s+1}" for s in group])
                f.write(f"      车组{i}: 站点[{stations_str}]\n")
                f.write(f"        车辆: 小车×{plan['n_small']} + 大车×{plan['n_large']}\n")
                f.write(f"        单次配送成本: {plan['total_trip_cost']:,.2f} 元\n")
            f.write("\n")
        
        # Top方案对比
        f.write("\n【Top 10 方案对比】\n\n")
        f.write(f"{'排名':<6} {'A':<4} {'B':<4} {'C':<4} {'D':<4} {'E':<4} {'总成本':<15}\n")
        f.write("-" * 50 + "\n")
        for i, sol in enumerate(global_result['top_solutions'][:10], 1):
            T = sol['T_combo']
            marker = " ← 最优" if i == 1 else ""
            f.write(f"{i:<6} {T['A']:<4} {T['B']:<4} {T['C']:<4} {T['D']:<4} {T['E']:<4} "
                   f"{sol['total_cost']:<15,.2f}{marker}\n")
    
    return {
        'optimal_json': optimal_file,
        'top_json': top_file,
        'report': report_file
    }


def print_final_summary(global_result: dict):
    """打印最终摘要"""
    optimal = global_result['optimal_solution']
    
    print("\n" + "="*70)
    print("🎉 美团物流优化系统 - 最终优化结果")
    print("="*70)
    
    print(f"\n💰 系统日总成本最小值: {optimal['total_cost']:,.2f} 元")
    print(f"\n📊 成本构成:")
    print(f"   总仓储成本: {optimal['total_storage_cost']:,.2f} 元 ({optimal['total_storage_cost']/optimal['total_cost']*100:.1f}%)")
    print(f"   总运输成本: {optimal['total_transport_cost']:,.2f} 元 ({optimal['total_transport_cost']/optimal['total_cost']*100:.1f}%)")
    
    print(f"\n📋 各城市最优配置:")
    print(f"{'城市':<6} {'订货周期T':<12} {'日总成本':<15} {'车辆数':<8}")
    print("-" * 50)
    for city, T in optimal['T_combo'].items():
        city_result = next(r for r in optimal['city_results'] if r['city_code'] == city)
        n_vehicles = city_result['route_plan']['n_vehicles']
        print(f"City {city:<3} {T:<12} {city_result['total_cost']:<15,.1f} {n_vehicles}")
    
    print("\n" + "="*70)
    print("✅ 优化完成！详细报告已保存到 output/ 目录")
    print("="*70 + "\n")


def main():
    """主程序"""
    print("\n" + "🚚"*35)
    print("美团物流优化系统")
    print("城市群零售网络物流与库存联合优化")
    print("🚚"*35 + "\n")
    
    # 1. 先运行各城市独立优化（快速预览）
    print("\n【阶段1】各城市独立优化分析...")
    city_results, independent_total = run_all_cities_analysis(verbose=True)
    
    # 2. 运行全局优化（完整搜索）
    print("\n【阶段2】全局联合优化搜索...")
    global_result = run_global_optimization(top_k=10, verbose=True)
    
    # 3. 生成详细报告
    print("\n【阶段3】生成详细报告...")
    output_dir = Path(__file__).parent / "output"
    report_files = generate_detailed_report(global_result, output_dir)
    
    # 4. 打印最终摘要
    print_final_summary(global_result)
    
    print(f"📁 报告文件已保存:")
    for name, path in report_files.items():
        print(f"   - {name}: {path}")
    
    return global_result


if __name__ == "__main__":
    result = main()
