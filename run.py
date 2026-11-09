"""
自动化测试主入口
===================
一键执行测试 → 生成 Allure 报告 → 更新仪表盘

用法：
    python run.py               # 运行所有测试
    python run.py api            # 只跑 API 测试
    python run.py ui             # 只跑 UI 测试
    python run.py integration    # 只跑集成测试
    python run.py smoke          # 只跑冒烟测试
    python run.py -m "api or smoke"  # 自定义标记
    python run.py --no-report    # 跑测试，不生成报告
    python run.py --open         # 跑完后打开仪表盘
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="自动化测试入口 — 执行测试 → 生成报告 → 更新仪表盘",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python run.py              # 全部测试\n"
               "  python run.py api          # API 测试\n"
               "  python run.py api -v       # API 测试 + 详细日志\n"
               "  python run.py --open       # 跑完打开仪表盘\n"
               "  python run.py --no-report  # 不生成报告（仅调试用）",
    )
    parser.add_argument(
        "scope", nargs="?", default="all",
        choices=["all", "api", "ui", "integration", "smoke"],
        help="测试范围 (默认: all)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="显示详细日志",
    )
    parser.add_argument(
        "-m", "--marker", type=str, default=None,
        help="pytest 标记表达式，如 'api or smoke'",
    )
    parser.add_argument(
        "--no-report", action="store_true",
        help="跳过 Allure 报告生成",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="运行结束后打开仪表盘",
    )
    parser.add_argument(
        "--args", type=str, default=None,
        help="透传给 pytest 的额外参数（用引号包裹）",
    )
    return parser.parse_args()


def build_pytest_args(args: argparse.Namespace) -> list[str]:
    """构建 pytest 命令行参数"""
    cmd = [sys.executable, "-m", "pytest"]

    # 测试路径 & 标记
    if args.scope == "all":
        cmd.append("tests/")
    elif args.scope == "smoke":
        cmd.extend(["-m", "smoke", "tests/"])
    else:
        cmd.append(f"tests/{args.scope}/")

    # 自定义标记覆盖 scope
    if args.marker:
        cmd.extend(["-m", args.marker])

    # 详细日志
    if args.verbose:
        cmd.append("-v")

    # 额外透传参数
    if args.args:
        cmd.extend(args.args.split())

    return cmd


def run_tests(cmd: list[str]) -> int:
    """执行 pytest，返回退出码"""
    print(f"\n{'=' * 60}")
    print(f"  🧪 开始执行测试...")
    print(f"  📁 目录: {PROJECT_ROOT}")
    print(f"  🔧 命令: {' '.join(cmd)}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        print(f"\n{'=' * 60}")
        print(f"  ✅ 全部测试通过!")
        print(f"{'=' * 60}\n")
    else:
        print(f"\n{'=' * 60}")
        print(f"  ❌ 测试执行完成，部分失败 (exit code: {result.returncode})")
        print(f"{'=' * 60}\n")

    return result.returncode


def open_report():
    """打开仪表盘"""
    dashboard = PROJECT_ROOT / "reports" / "dashboard" / "index.html"
    if dashboard.exists():
        print(f"  📊 打开仪表盘: {dashboard}")
        import webbrowser
        webbrowser.open(str(dashboard))
    else:
        print(f"  ⚠️  仪表盘未找到，请先运行测试: {dashboard}")


def main():
    args = parse_args()
    pytest_cmd = build_pytest_args(args)

    # 如果需要跳过报告，设置环境变量让 conftest.py 识别
    if args.no_report:
        import os
        os.environ["HERMES_SKIP_REPORT"] = "1"

    exit_code = run_tests(pytest_cmd)

    # 打开仪表盘
    if args.open and exit_code == 0:
        open_report()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
