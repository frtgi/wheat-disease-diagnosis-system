"""
数据库迁移执行脚本
提供便捷的迁移命令执行入口
"""
import sys
import argparse
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd: list, cwd: str = None) -> int:
    """
    执行命令并实时输出结果
    
    参数:
        cmd: 要执行的命令列表
        cwd: 工作目录
    
    返回:
        int: 命令退出码
    """
    print(f"执行命令: {' '.join(cmd)}")
    print("=" * 50)
    
    result = subprocess.run(
        cmd,
        cwd=cwd or str(project_root),
        shell=False
    )
    
    return result.returncode


def check_alembic_installed() -> bool:
    """
    检查 Alembic 是否已安装
    
    返回:
        bool: 是否已安装
    """
    try:
        import alembic
        return True
    except ImportError:
        print("❌ Alembic 未安装，请先安装: pip install alembic")
        return False


def upgrade(revision: str = "head") -> int:
    """
    升级数据库到指定版本
    
    参数:
        revision: 目标版本号，默认为 head（最新版本）
    
    返回:
        int: 命令退出码
    """
    if not check_alembic_installed():
        return 1
    
    print(f"\n升级数据库到版本: {revision}")
    return run_command(["alembic", "upgrade", revision])


def downgrade(revision: str = "-1") -> int:
    """
    回滚数据库到指定版本
    
    参数:
        revision: 目标版本号，默认为 -1（回滚一个版本）
    
    返回:
        int: 命令退出码
    """
    if not check_alembic_installed():
        return 1
    
    print(f"\n回滚数据库到版本: {revision}")
    return run_command(["alembic", "downgrade", revision])


def current() -> int:
    """
    显示当前数据库版本
    
    返回:
        int: 命令退出码
    """
    if not check_alembic_installed():
        return 1
    
    print("\n当前数据库版本:")
    return run_command(["alembic", "current"])


def history() -> int:
    """
    显示迁移历史
    
    返回:
        int: 命令退出码
    """
    if not check_alembic_installed():
        return 1
    
    print("\n迁移历史:")
    return run_command(["alembic", "history"])


def revision(message: str, autogenerate: bool = True) -> int:
    """
    创建新的迁移脚本
    
    参数:
        message: 迁移说明信息
        autogenerate: 是否自动检测模型变更
    
    返回:
        int: 命令退出码
    """
    if not check_alembic_installed():
        return 1
    
    print(f"\n创建新迁移: {message}")
    cmd = ["alembic", "revision", "-m", message]
    if autogenerate:
        cmd.append("--autogenerate")
    return run_command(cmd)


def stamp(revision: str = "head") -> int:
    """
    标记数据库版本（不执行迁移）
    
    用于将现有数据库标记为最新版本，适用于：
    - 已存在数据库表，首次使用迁移系统
    - 手动修复迁移状态
    
    参数:
        revision: 要标记的版本号
    
    返回:
        int: 命令退出码
    """
    if not check_alembic_installed():
        return 1
    
    print(f"\n标记数据库版本: {revision}")
    return run_command(["alembic", "stamp", revision])


def main():
    """
    主函数 - 解析命令行参数并执行相应操作
    """
    parser = argparse.ArgumentParser(
        description="数据库迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_migrations.py upgrade          # 升级到最新版本
  python run_migrations.py upgrade 001      # 升级到指定版本
  python run_migrations.py downgrade        # 回滚一个版本
  python run_migrations.py downgrade base   # 回滚到初始状态
  python run_migrations.py current          # 查看当前版本
  python run_migrations.py history          # 查看迁移历史
  python run_migrations.py revision "添加新表"  # 创建新迁移
  python run_migrations.py stamp            # 标记当前版本为最新
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    upgrade_parser = subparsers.add_parser("upgrade", help="升级数据库")
    upgrade_parser.add_argument("revision", nargs="?", default="head", help="目标版本")
    
    downgrade_parser = subparsers.add_parser("downgrade", help="回滚数据库")
    downgrade_parser.add_argument("revision", nargs="?", default="-1", help="目标版本")
    
    subparsers.add_parser("current", help="显示当前版本")
    subparsers.add_parser("history", help="显示迁移历史")
    
    revision_parser = subparsers.add_parser("revision", help="创建新迁移")
    revision_parser.add_argument("message", help="迁移说明")
    revision_parser.add_argument("--no-autogenerate", action="store_true", help="不自动检测变更")
    
    stamp_parser = subparsers.add_parser("stamp", help="标记数据库版本")
    stamp_parser.add_argument("revision", nargs="?", default="head", help="版本号")
    
    args = parser.parse_args()
    
    if args.command == "upgrade":
        return upgrade(args.revision)
    elif args.command == "downgrade":
        return downgrade(args.revision)
    elif args.command == "current":
        return current()
    elif args.command == "history":
        return history()
    elif args.command == "revision":
        return revision(args.message, autogenerate=not args.no_autogenerate)
    elif args.command == "stamp":
        return stamp(args.revision)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
