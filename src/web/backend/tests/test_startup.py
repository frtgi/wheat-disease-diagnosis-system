"""
启动流程测试脚本

测试启动管理器、AI 预加载和健康检查端点
"""
import requests
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_startup_status() -> Dict[str, Any]:
    """测试启动状态端点"""
    print_section("测试 1: 启动状态检查 (/health/startup)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/startup", timeout=5)
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"启动状态：{data.get('status')}")
            print(f"总体进度：{data.get('progress')}%")
            print(f"当前阶段：{data.get('phase')}")
            print(f"已用时间：{data.get('elapsed_time', 'N/A')}秒")
            print(f"预计剩余：{data.get('estimated_remaining_time', 'N/A')}秒")
            
            if 'components' in data:
                print(f"\n组件状态:")
                for name, info in data['components'].items():
                    status = info.get('status', 'unknown')
                    progress = info.get('progress', 0)
                    print(f"  - {name}: {status} ({progress}%)")
            
            return {"success": True, "data": data}
        else:
            print(f"请求失败：{response.text}")
            return {"success": False, "error": response.text}
    
    except Exception as e:
        print(f"测试失败：{e}")
        return {"success": False, "error": str(e)}

def test_readiness_check() -> Dict[str, Any]:
    """测试就绪状态端点"""
    print_section("测试 2: 就绪状态检查 (/health/ready)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/ready", timeout=5)
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"是否就绪：{data.get('ready')}")
            print(f"是否降级：{data.get('degraded')}")
            print(f"是否失败：{data.get('failed')}")
            print(f"状态：{data.get('status')}")
            print(f"消息：{data.get('message')}")
            
            if 'critical_components' in data:
                print(f"\n关键组件:")
                for name, ready in data['critical_components'].items():
                    status = "✓" if ready else "✗"
                    print(f"  {status} {name}")
            
            return {"success": True, "data": data}
        else:
            print(f"请求失败：{response.text}")
            return {"success": False, "error": response.text}
    
    except Exception as e:
        print(f"测试失败：{e}")
        return {"success": False, "error": str(e)}

def test_components_status() -> Dict[str, Any]:
    """测试组件状态端点"""
    print_section("测试 3: 组件状态检查 (/health/components)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/components", timeout=5)
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"总体状态：{data.get('status')}")
            
            if 'summary' in data:
                summary = data['summary']
                print(f"组件总数：{summary.get('total')}")
                print(f"就绪：{summary.get('ready')}")
                print(f"失败：{summary.get('failed')}")
                print(f"降级：{summary.get('degraded')}")
            
            if 'components' in data:
                print(f"\n详细组件状态:")
                for name, info in data['components'].items():
                    status = info.get('status', 'unknown')
                    icon = "✓" if status == "ready" else ("⚠" if status == "degraded" else "✗")
                    print(f"\n  {icon} {name}: {status}")
                    
                    # 打印其他信息
                    for key, value in info.items():
                        if key != 'status':
                            print(f"      {key}: {value}")
            
            return {"success": True, "data": data}
        else:
            print(f"请求失败：{response.text}")
            return {"success": False, "error": response.text}
    
    except Exception as e:
        print(f"测试失败：{e}")
        return {"success": False, "error": str(e)}

def test_ai_health() -> Dict[str, Any]:
    """测试 AI 健康检查"""
    print_section("测试 4: AI 健康检查 (/diagnosis/health/ai)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/diagnosis/health/ai", timeout=5)
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"YOLO 加载状态：{data.get('yolo', {}).get('is_loaded', False)}")
            print(f"Qwen 加载状态：{data.get('qwen', {}).get('is_loaded', False)}")
            print(f"总体状态：{data.get('status')}")
            
            if 'yolo' in data and data['yolo'].get('is_loaded'):
                print(f"\nYOLO 信息:")
                print(f"  模型路径：{data['yolo'].get('model_path', 'N/A')}")
                print(f"  置信度阈值：{data['yolo'].get('confidence_threshold', 0.5)}")
            
            if 'qwen' in data and data['qwen'].get('is_loaded'):
                print(f"\nQwen 信息:")
                print(f"  模型路径：{data['qwen'].get('model_path', 'N/A')}")
                print(f"  设备：{data['qwen'].get('device', 'cpu')}")
                print(f"  INT4 量化：{data['qwen'].get('int4_quantization', False)}")
            
            return {"success": True, "data": data}
        else:
            print(f"请求失败：{response.text}")
            return {"success": False, "error": response.text}
    
    except Exception as e:
        print(f"测试失败：{e}")
        return {"success": False, "error": str(e)}

def test_database_health() -> Dict[str, Any]:
    """测试数据库健康检查"""
    print_section("测试 5: 数据库健康检查 (/health/database)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/database", timeout=5)
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"数据库状态：{data.get('status')}")
            print(f"数据库名：{data.get('database')}")
            print(f"连接时间：{data.get('connection_time_ms')}ms")
            print(f"表数量：{data.get('table_count')}")
            
            return {"success": True, "data": data}
        else:
            print(f"请求失败：{response.text}")
            return {"success": False, "error": response.text}
    
    except Exception as e:
        print(f"测试失败：{e}")
        return {"success": False, "error": str(e)}

def run_all_tests():
    """运行所有测试"""
    print_section("启动流程测试开始")
    print(f"目标地址：{BASE_URL}")
    print(f"测试时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "startup_status": None,
        "readiness_check": None,
        "components_status": None,
        "ai_health": None,
        "database_health": None
    }
    
    # 运行测试
    results["startup_status"] = test_startup_status()
    time.sleep(0.5)
    
    results["readiness_check"] = test_readiness_check()
    time.sleep(0.5)
    
    results["components_status"] = test_components_status()
    time.sleep(0.5)
    
    results["ai_health"] = test_ai_health()
    time.sleep(0.5)
    
    results["database_health"] = test_database_health()
    
    # 总结
    print_section("测试总结")
    
    passed = sum(1 for r in results.values() if r and r.get("success"))
    total = len(results)
    
    print(f"通过：{passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有测试通过！")
    else:
        print("\n✗ 部分测试失败:")
        for name, result in results.items():
            if not result or not result.get("success"):
                print(f"  - {name}: {result.get('error', 'unknown') if result else 'no response'}")
    
    # 保存结果
    with open("startup_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "results": results,
            "summary": {
                "passed": passed,
                "total": total,
                "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A"
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到：startup_test_results.json")
    
    return passed == total

if __name__ == "__main__":
    # 等待服务启动
    print("等待服务启动...")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("服务已响应！")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("警告：服务可能未启动或响应超时")
        print("请确保后端服务正在运行：python -m uvicorn app.main:app --reload")
    
    # 运行测试
    success = run_all_tests()
    exit(0 if success else 1)
