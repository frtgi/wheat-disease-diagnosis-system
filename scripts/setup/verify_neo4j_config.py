# -*- coding: utf-8 -*-
"""
Neo4j 环境变量配置验证脚本

用于验证 Neo4j 环境变量是否正确配置，并测试数据库连接。
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def check_env_variables():
    """
    检查 Neo4j 环境变量是否已设置
    
    :return: 配置字典
    """
    print("\n" + "=" * 60)
    print("📋 检查 Neo4j 环境变量配置")
    print("=" * 60)
    
    required_vars = {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": None,
        "NEO4J_DATABASE": "neo4j",
        "NEO4J_MAX_CONNECTION_POOL_SIZE": "50",
        "NEO4J_CONNECTION_TIMEOUT": "30"
    }
    
    config = {}
    all_set = True
    
    for var, default in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == "NEO4J_PASSWORD":
                print(f"  ✅ {var} = ******")
            else:
                print(f"  ✅ {var} = {value}")
            config[var] = value
        else:
            if default:
                print(f"  ⚠️  {var} = <未设置，使用默认值: {default}>")
                config[var] = default
            else:
                print(f"  ❌ {var} = <未设置>")
                all_set = False
    
    print()
    if all_set:
        print("✅ 所有必需的环境变量已设置")
    else:
        print("⚠️  部分环境变量未设置，请检查配置")
    
    return config


def test_connection(config):
    """
    测试 Neo4j 数据库连接
    
    :param config: 配置字典
    :return: 是否连接成功
    """
    print("\n" + "=" * 60)
    print("🔌 测试 Neo4j 连接")
    print("=" * 60)
    
    try:
        from neo4j import GraphDatabase
        
        uri = config.get("NEO4J_URI", "bolt://localhost:7687")
        user = config.get("NEO4J_USER", "neo4j")
        password = config.get("NEO4J_PASSWORD", "")
        
        print(f"  连接 URI: {uri}")
        print(f"  用户名: {user}")
        print(f"  正在连接...")
        
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            connection_timeout=float(config.get("NEO4J_CONNECTION_TIMEOUT", "30"))
        )
        
        driver.verify_connectivity()
        print("  ✅ 连接成功!")
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
            print("  ✅ 查询测试成功!")
            
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"  📊 数据库节点数: {count}")
        
        driver.close()
        return True
        
    except ImportError:
        print("  ❌ neo4j 包未安装，请运行: pip install neo4j")
        return False
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False


def test_knowledge_agent():
    """
    测试 KnowledgeAgent 类是否正常工作
    
    :return: 是否测试成功
    """
    print("\n" + "=" * 60)
    print("🧪 测试 KnowledgeAgent 模块")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        env_file = project_root / "src" / "web" / "backend" / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            print(f"  ✅ 已加载 .env 文件: {env_file}")
        
        from graph.graph_engine import KnowledgeAgent, get_neo4j_config
        
        config = get_neo4j_config()
        print(f"  配置信息:")
        print(f"    URI: {config['uri']}")
        print(f"    用户: {config['user']}")
        print(f"    数据库: {config['database']}")
        
        print("  正在初始化 KnowledgeAgent...")
        agent = KnowledgeAgent()
        
        print("  测试查询...")
        details = agent.get_disease_details("条锈病")
        if details:
            print(f"  ✅ 查询成功: {details}")
        else:
            print("  ⚠️  未找到病害信息")
        
        agent.close()
        print("  ✅ KnowledgeAgent 测试通过!")
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_setup_instructions():
    """
    打印环境变量设置说明
    """
    print("\n" + "=" * 60)
    print("📖 环境变量设置说明")
    print("=" * 60)
    print("""
方法 1: 使用 PowerShell 脚本 (推荐)
  cd WheatAgent/scripts/setup
  ./setup_neo4j_env.ps1 -Action setup

方法 2: 手动设置环境变量
  # PowerShell (用户级)
  [Environment]::SetEnvironmentVariable("NEO4J_URI", "bolt://localhost:7687", "User")
  [Environment]::SetEnvironmentVariable("NEO4J_USER", "neo4j", "User")
  [Environment]::SetEnvironmentVariable("NEO4J_PASSWORD", "your_password", "User")

方法 3: 使用 .env 文件
  复制 src/web/backend/.env.example 为 .env
  编辑 .env 文件，设置 NEO4J_* 相关变量

方法 4: 临时设置 (仅当前会话有效)
  $env:NEO4J_URI = "bolt://localhost:7687"
  $env:NEO4J_USER = "neo4j"
  $env:NEO4J_PASSWORD = "your_password"
""")


def main():
    """
    主函数
    """
    print("\n" + "=" * 60)
    print("    Neo4j 环境变量配置验证工具")
    print("=" * 60)
    
    config = check_env_variables()
    
    if not config.get("NEO4J_PASSWORD"):
        print("\n⚠️  未设置 NEO4J_PASSWORD，请先设置密码")
        print_setup_instructions()
        return 1
    
    connection_ok = test_connection(config)
    
    if connection_ok:
        test_knowledge_agent()
    
    print("\n" + "=" * 60)
    if connection_ok:
        print("✅ 验证完成 - Neo4j 配置正确")
    else:
        print("❌ 验证失败 - 请检查 Neo4j 配置")
    print("=" * 60 + "\n")
    
    return 0 if connection_ok else 1


if __name__ == "__main__":
    sys.exit(main())
