"""
全局 pytest 配置文件

提供项目中所有测试共享的 fixture 和钩子：
- 配置加载
- Allure 报告设置（环境信息、运行参数）
- 测试用例前后置处理
- 失败自动截图（UI 测试）

此文件位于项目根目录，pytest 会自动发现。
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import allure
import pytest

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
#  会话级：测试运行前的全局设置
# ============================================================

def pytest_sessionstart(session):
    """
    测试会话开始时执行：
    1. 创建报告目录
    2. 清理旧的 allure-results（避免累积）
    3. 复制上一份报告的 history 数据（用于趋势图）
    4. 记录运行环境信息
    """
    # 清理旧的 allure-results，确保每次运行数据独立
    allure_dir = settings.get_report_dir()
    if allure_dir.exists():
        import shutil
        for f in allure_dir.iterdir():
            if f.is_file():
                f.unlink()
            elif f.is_dir() and f.name != "history":
                shutil.rmtree(f)
    allure_dir.mkdir(parents=True, exist_ok=True)
    logger.info("📁 Allure 结果目录已重置: %s", allure_dir)

    # 从上一份报告复制 history 数据（用于 Allure 趋势图）
    _copy_history_from_last_report()

    # 创建日志目录
    log_path = settings.get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 记录环境信息到 Allure
    _write_allure_environment()

    logger.info("🚀 测试会话启动 — 环境: %s, 目标: %s", settings.env, settings.base_url)


def _copy_history_from_last_report():
    """
    从最新的历史报告中复制 history/ 目录到 allure-results
    这样 Allure 生成的趋势图能看到历史数据
    """
    reports_dir = settings.project_root / "reports" / "allure-reports"
    if not reports_dir.exists():
        return

    # 找到最新的报告目录（按时间戳名称排序）
    history_dirs = sorted(
        [d for d in reports_dir.iterdir() if d.is_dir() and d.name[0].isdigit()],
        reverse=True,
    )
    if not history_dirs:
        return

    latest_report = history_dirs[0]
    history_src = latest_report / "history"
    if not history_src.exists():
        return

    # 复制 history 到 allure-results
    allure_dir = settings.get_report_dir()
    import shutil
    shutil.copytree(str(history_src), str(allure_dir / "history"), dirs_exist_ok=True)
    logger.info("📜 已从 %s 复制历史趋势数据", latest_report.name)


def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束时执行：
    1. 输出测试结果摘要
    2. 自动生成 Allure HTML 报告（带时间戳目录）
    3. 保存报告元数据（供仪表盘使用）
    4. 更新历史报告仪表盘
    """
    logger.info("🏁 测试会话结束 — 退出码: %d", exitstatus)

    # 自动生成 Allure HTML 报告
    report_dir = _generate_allure_report()
    if report_dir is None:
        return

    # 保存报告元数据（仪表盘使用）
    _save_report_metadata(report_dir)

    # 更新历史报告仪表盘
    _update_report_dashboard()


def _generate_allure_report() -> Optional[Path]:
    """
    生成 Allure HTML 报告到 reports/allure-reports/<timestamp>/

    使用 allure generate 命令（Java 版 Allure CLI）。
    报告目录名格式：yy-mm-dd_hh-mm-ss
    例如：25-07-15_14-30-45

    Returns:
        报告目录路径，失败返回 None
    """
    allure_results_dir = settings.get_report_dir()
    if not allure_results_dir.exists() or not list(allure_results_dir.iterdir()):
        logger.warning("Allure 结果目录为空，跳过报告生成: %s", allure_results_dir)
        return None

    # 生成时间戳目录名：yy-mm-dd_hh-mm-ss
    timestamp = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
    report_dir = settings.project_root / "reports" / "allure-reports" / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)

    logger.info("📊 正在生成 Allure 报告...")
    logger.info("   结果目录: %s", allure_results_dir)
    logger.info("   报告目录: %s", report_dir)

    # Allure CLI 路径（解压到本地固定目录）
    allure_cmd = str(Path.home() / "allure-cli" / "allure-2.33.0" / "bin" / "allure.bat")

    try:
        result = subprocess.run(
            [allure_cmd, "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("✅ Allure 报告生成成功: %s", report_dir)
            return report_dir
        else:
            logger.error("❌ Allure 报告生成失败: %s", result.stderr.strip())
            return None
    except FileNotFoundError:
        logger.error("❌ 未找到 allure 命令: %s", allure_cmd)
        return None
    except subprocess.TimeoutExpired:
        logger.error("❌ Allure 报告生成超时")
        return None
    except Exception as e:
        logger.error("❌ Allure 报告生成异常: %s", e)
        return None


def _write_allure_environment():
    """向 Allure 报告写入环境信息"""
    env_path = settings.get_report_dir() / "environment.properties"
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"Environment={settings.env}\n")
            f.write(f"Base_URL={settings.base_url}\n")
            f.write(f"Browser={settings.ui.browser}\n")
            f.write(f"Headless={settings.ui.headless}\n")
            f.write(f"Python=3.12\n")
            f.write(f"Timestamp={datetime.now().isoformat()}\n")
        logger.info("📝 Allure 环境信息已写入: %s", env_path)
    except Exception as e:
        logger.warning("写入 Allure 环境信息失败: %s", e)


def _save_report_metadata(report_dir: Path):
    """
    保存报告元数据到 report.json

    从 Allure 生成的 widgets/summary.json 中提取关键指标，
    记录到 report.json 供仪表盘使用。

    Args:
        report_dir: 报告目录路径
    """
    summary_file = report_dir / "widgets" / "summary.json"
    if not summary_file.exists():
        logger.warning("报告元数据文件不存在: %s", summary_file)
        return

    try:
        import json
        summary = json.loads(summary_file.read_text(encoding="utf-8"))

        # 读取环境信息（Allure 格式：{"values": ["xxx"], "name": "xxx"}）
        env = {}
        env_file = report_dir / "widgets" / "environment.json"
        if env_file.exists():
            env_data = json.loads(env_file.read_text(encoding="utf-8"))
            for item in env_data:
                values = item.get("values", [])
                env[item.get("name", "")] = values[0] if values else ""

        # 提取运行时间
        run_time = summary.get("time", {})
        start_ms = run_time.get("start", 0)
        stop_ms = run_time.get("stop", 0)
        duration_ms = run_time.get("duration", 0)

        # 从目录名解析时间戳
        ts = report_dir.name

        metadata = {
            "timestamp": ts,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": datetime.fromtimestamp(start_ms / 1000).strftime("%H:%M:%S") if start_ms else "",
            "duration_sec": round(duration_ms / 1000, 1),
            "statistic": summary.get("statistic", {}),
            "environment": env,
        }

        meta_path = report_dir / "report.json"
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("📋 报告元数据已保存: %s", meta_path)
    except Exception as e:
        logger.warning("保存报告元数据失败: %s", e)


def _update_report_dashboard():
    """
    更新历史报告仪表盘

    扫描 reports/allure-reports/ 下所有报告，生成 dashboard/index.html
    """
    try:
        from utils.report_dashboard import generate_dashboard
        generate_dashboard()
    except ImportError:
        logger.warning("仪表盘生成器未找到，跳过")
    except Exception as e:
        logger.warning("仪表盘更新失败: %s", e)


# ============================================================
#  测试用例级别：前后置处理
# ============================================================

@pytest.fixture(autouse=True)
def test_case_log(request):
    """
    自动 fixture：记录每个测试用例的开始和结束
    测试名称显示在控制台和 Allure 报告中
    """
    test_name = request.node.name
    test_doc = request.node.function.__doc__ or ""
    logger.info("=" * 60)
    logger.info("🧪 开始测试: %s", test_name)
    if test_doc:
        logger.info("   描述: %s", test_doc.strip())

    # 将测试描述附加到 Allure 报告
    if test_doc:
        allure.dynamic.description(test_doc.strip())

    yield

    logger.info("✅ 测试结束: %s", test_name)


@pytest.fixture(autouse=True)
def attach_test_metadata(request):
    """
    自动 fixture：将 pytest markers 作为 Allure 标签
    方便在 Allure 报告中按标签筛选
    """
    markers = [m.name for m in request.node.iter_markers()]
    for marker in markers:
        if marker not in ("parametrize", "fixture", "asyncio", "filter"):
            allure.dynamic.tag(marker)


# ============================================================
#  命令行选项：支持 --env 切换环境
# ============================================================

def pytest_addoption(parser):
    """添加自定义命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        help="测试环境: dev / staging / prod",
    )


def pytest_configure(config):
    """根据 --env 参数加载对应配置，设置 Allure 输出目录"""
    env = config.getvalue("env")
    settings.env = env
    # 重新加载配置
    from config.settings import Settings
    new_settings = Settings.load_from_yaml()
    settings.__dict__.update(new_settings.__dict__)

    # 设置 Allure 结果输出目录（与 settings.get_report_dir() 保持一致）
    allure_dir = settings.get_report_dir()
    config.option.allure_report_dir = str(allure_dir)

    # 注册自定义标记
    config.addinivalue_line("markers", "smoke: 冒烟测试 — 核心功能验证")
    config.addinivalue_line("markers", "regression: 回归测试")


# ============================================================
#  pytest 钩子：测试失败时自动附加信息到 Allure
# ============================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试失败时，自动截图（UI 测试）并附加到 Allure 报告
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # 检查是否有 page fixture
        page = item.funcargs.get("page")
        if page:
            try:
                screenshot_dir = settings.project_root / "reports" / "screenshots"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = screenshot_dir / f"FAILED_{item.name}_{timestamp}.png"
                page.screenshot(path=str(screenshot_path))
                # 附加到 Allure
                allure.attach.file(
                    str(screenshot_path),
                    name=f"失败截图: {item.name}",
                    attachment_type=allure.attachment_type.PNG,
                )
                logger.info("📸 失败截图: %s", screenshot_path)
            except Exception as e:
                logger.warning("截图失败: %s", e)