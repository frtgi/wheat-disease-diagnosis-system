"""
融合诊断 SSE 数据流测试
验证后端到前端的数据传输是否正确
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


async def test_sse_diagnosis():
    """测试 SSE 诊断数据流"""
    base_url = "http://localhost:8000"
    api_prefix = "/api/v1"
    
    print("=" * 60)
    print("🧪 融合诊断 SSE 数据流测试")
    print("=" * 60)
    
    url = f"{base_url}{api_prefix}/diagnosis/fusion/stream?symptoms=叶片发黄"
    
    print(f"\n📡 连接 SSE 端点: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    print(f"❌ 连接失败: {response.status_code}")
                    return False
                
                print(f"✅ 连接成功，Content-Type: {response.headers.get('content-type')}")
                
                events = []
                current_event = None
                current_data = []
                
                async for line in response.aiter_lines():
                    line = line.strip()
                    
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                        current_data = []
                    elif line.startswith("data:"):
                        current_data.append(line[5:].strip())
                    elif line == "" and current_event:
                        # 事件结束，处理数据
                        data_str = "\n".join(current_data)
                        try:
                            data = json.loads(data_str)
                            events.append({
                                "event": current_event,
                                "data": data
                            })
                            
                            print(f"\n📨 事件: {current_event}")
                            print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                            
                            if current_event == "complete":
                                print("\n" + "=" * 60)
                                print("📊 Complete 事件分析")
                                print("=" * 60)
                                
                                if "success" in data:
                                    print(f"✅ success 字段存在: {data['success']}")
                                else:
                                    print("❌ success 字段缺失")
                                
                                if "diagnosis" in data:
                                    print(f"✅ diagnosis 字段存在")
                                    diagnosis = data["diagnosis"]
                                    print(f"   - disease_name: {diagnosis.get('disease_name', 'N/A')}")
                                    print(f"   - confidence: {diagnosis.get('confidence', 'N/A')}")
                                    print(f"   - recommendations: {len(diagnosis.get('recommendations', []))} 条")
                                else:
                                    print("❌ diagnosis 字段缺失")
                                
                                if "reasoning_chain" in data:
                                    print(f"✅ reasoning_chain 字段存在: {len(data['reasoning_chain'])} 步")
                                else:
                                    print("⚠️ reasoning_chain 字段缺失")
                                
                                return True
                                
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON 解析失败: {e}")
                            print(f"   原始数据: {data_str[:200]}")
                        
                        current_event = None
                        current_data = []
                
                print(f"\n📋 共收到 {len(events)} 个事件")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_sse_diagnosis())
    sys.exit(0 if success else 1)
