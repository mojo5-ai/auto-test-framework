"""历史报告仪表盘生成器

扫描 reports/allure-reports/ 下所有历史报告，生成一个 dashboard/index.html，
在单一页面中按时间线展示所有测试报告，支持搜索、分页、趋势图和状态筛选。

用法：
    from utils.report_dashboard import generate_dashboard
    generate_dashboard()

输出： reports/allure-reports/index.html（仪表盘入口）
      reports/allure-reports/dashboard-data.json（报告元数据汇总）
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def scan_reports(reports_dir: Path) -> list[dict]:
    """
    扫描所有历史报告目录，收集元数据

    Args:
        reports_dir: reports/allure-reports/ 目录

    Returns:
        按时间倒序排列的报告元数据列表
    """
    reports = []
    if not reports_dir.exists():
        return reports

    for subdir in sorted(reports_dir.iterdir(), reverse=True):
        if not subdir.is_dir():
            continue
        name = subdir.name

        # 跳过非时间戳目录
        if not name[0].isdigit():
            continue

        # 优先读取 report.json（更完整的元数据）
        meta_file = subdir / "report.json"
        summary_file = subdir / "widgets" / "summary.json"

        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                reports.append(meta)
                continue
            except Exception:
                pass

        # 降级读取 summary.json
        if summary_file.exists():
            try:
                summary = json.loads(summary_file.read_text(encoding="utf-8"))
                stat = summary.get("statistic", {})
                run_time = summary.get("time", {})
                duration_ms = run_time.get("duration", 0)
                reports.append({
                    "timestamp": name,
                    "datetime": name.replace("_", " ").replace("-", "-"),
                    "duration_sec": round(duration_ms / 1000, 1),
                    "statistic": stat,
                    "environment": {},
                })
            except Exception:
                pass

    return reports


def _calc_summary(reports: list[dict]) -> dict:
    """计算所有报告的汇总统计"""
    total_runs = len(reports)
    total_passed = sum(r.get("statistic", {}).get("passed", 0) for r in reports)
    total_failed = sum(r.get("statistic", {}).get("failed", 0) for r in reports)
    total_broken = sum(r.get("statistic", {}).get("broken", 0) for r in reports)
    total_skipped = sum(r.get("statistic", {}).get("skipped", 0) for r in reports)
    total_cases = total_passed + total_failed + total_broken + total_skipped

    latest_pass_rate = 0
    if reports:
        latest = reports[0].get("statistic", {})
        lt = latest.get("passed", 0) + latest.get("failed", 0) + latest.get("broken", 0) + latest.get("skipped", 0)
        if lt > 0:
            latest_pass_rate = round(latest["passed"] / lt * 100, 1)

    return {
        "total_runs": total_runs,
        "total_cases": total_cases,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "total_broken": total_broken,
        "total_skipped": total_skipped,
        "latest_pass_rate": latest_pass_rate,
    }


def generate_dashboard():
    """
    生成历史报告仪表盘

    输出：
        reports/dashboard/index.html              → 主仪表盘入口
        reports/dashboard/dashboard-data.json     → 报告元数据（供前端使用）
    """
    scans_dir = settings.project_root / "reports" / "allure-reports"
    output_dir = settings.project_root / "reports" / "dashboard"
    reports = scan_reports(scans_dir)

    if not reports:
        logger.warning("未找到历史报告，跳过仪表盘生成")
        _generate_empty_dashboard(output_dir)
        return

    summary = _calc_summary(reports)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存数据文件供前端使用
    data_file = output_dir / "dashboard-data.json"
    data_file.write_text(
        json.dumps({"summary": summary, "reports": reports}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 生成 HTML
    html = _build_dashboard_html(reports, summary)
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")

    logger.info("✅ 仪表盘已生成: %s", index_path)
    logger.info("   共 %d 份历史报告, %d 个测试用例, 最新通过率 %s%%",
                summary["total_runs"], summary["total_cases"], summary["latest_pass_rate"])


def _card_color(pass_rate: float) -> str:
    """根据通过率返回卡片颜色"""
    if pass_rate == 100 or pass_rate >= 90:
        return "#4CAF50"
    elif pass_rate == 0:
        return "#f44336"
    return "#FF9800"


def _build_dashboard_html(reports: list[dict], summary: dict) -> str:
    """构建仪表盘 HTML 页面（JS 动态渲染卡片、搜索、分页、趋势图、状态筛选）"""

    # ===== 预计算每张卡片的颜色和通过率，嵌入到报告数据中 =====
    for r in reports:
        stat = r.get("statistic", {})
        passed = stat.get("passed", 0)
        total = passed + stat.get("failed", 0) + stat.get("broken", 0) + stat.get("skipped", 0)
        r["_pass_rate"] = round(passed / total * 100, 1) if total > 0 else 0
        r["_color"] = _card_color(r["_pass_rate"])
        r["_display_time"] = r.get("timestamp", "").replace("_", " ")

    # ===== 序列化报告数据供 JS 使用 =====
    reports_json = json.dumps(reports, ensure_ascii=False)

    # ===== 页面 HTML =====
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>历史测试报告仪表盘</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f1a; color: #e0e0e0; min-height: 100vh; }}
.header {{ background: linear-gradient(135deg, #1a1a3e 0%, #2d1b69 100%); padding: 40px 30px 30px; text-align: center; }}
.header h1 {{ font-size: 32px; margin-bottom: 8px; }}
.header .subtitle {{ color: #aaa; font-size: 14px; }}
.summary-bar {{ display: flex; justify-content: center; gap: 40px; padding: 25px; background: #1a1a2e; flex-wrap: wrap; }}
.summary-item {{ text-align: center; }}
.summary-item .num {{ font-size: 30px; font-weight: bold; }}
.summary-item .label {{ font-size: 13px; color: #999; margin-top: 4px; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

/* 图表区 */
.chart-section {{ background: #1a1a2e; border-radius: 12px; padding: 25px; margin-bottom: 25px; position: relative; }}
.chart-section h2 {{ font-size: 18px; margin-bottom: 15px; color: #ccc; }}
.chart-wrap {{ height: 220px; position: relative; }}

/* 图表浮窗 */
.chart-tooltip {{ display: none; position: absolute; background: #1a1a2e; border: 1px solid #667eea; border-radius: 12px; padding: 14px; font-size: 13px; line-height: 1.6; pointer-events: none; z-index: 50; min-width: 220px; box-shadow: 0 8px 25px rgba(0,0,0,0.5); }}
.chart-tooltip .tt-title {{ font-weight: 600; color: #e0e0e0; margin-bottom: 4px; }}
.chart-tooltip .tt-rate {{ font-size: 18px; font-weight: bold; }}
.chart-tooltip .tt-row {{ display: flex; gap: 12px; color: #aaa; }}
.chart-tooltip .tt-stats {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 4px; }}

/* 工具栏 */
.toolbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }}
.toolbar h2 {{ font-size: 18px; color: #ccc; }}
.toolbar .controls {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
.toolbar input {{ background: #2a2a3e; border: 1px solid #444; color: #e0e0e0; padding: 8px 14px; border-radius: 8px; font-size: 14px; outline: none; width: 200px; }}
.toolbar input:focus {{ border-color: #667eea; }}
.toolbar select {{ background: #2a2a3e; border: 1px solid #444; color: #e0e0e0; padding: 8px 12px; border-radius: 8px; font-size: 14px; outline: none; cursor: pointer; }}
.toolbar select:focus {{ border-color: #667eea; }}
.toolbar button {{ background: #667eea; border: none; color: white; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; white-space: nowrap; }}
.toolbar button:hover {{ background: #5a6fd6; }}

/* 日期筛选弹窗（日历组件） */
.date-filter-wrap {{ position: relative; }}
.date-filter-btn {{ cursor: pointer; padding: 8px 14px; background: #2a2a3e; border: 1px solid #444; border-radius: 8px; font-size: 14px; white-space: nowrap; min-width: 135px; text-align: center; }}
.date-filter-btn:hover {{ border-color: #667eea; }}
.date-filter-btn.active {{ border-color: #667eea; background: #252540; }}
.date-picker-popup {{ display: none; position: absolute; top: 105%; left: 0; background: #1a1a2e; border: 1px solid #555; border-radius: 12px; z-index: 100; box-shadow: 0 8px 30px rgba(0,0,0,0.5); overflow: hidden; }}
.date-picker-popup.show {{ display: flex; }}
/* 左侧快捷 */
.dp-sidebar {{ display: flex; flex-direction: column; gap: 4px; padding: 16px 10px; background: #15152a; min-width: 100px; border-right: 1px solid #333; }}
.dp-sidebar-title {{ font-size: 13px; color: #888; margin-bottom: 6px; padding-left: 4px; }}
.dp-quick {{ background: transparent; border: none; color: #ccc; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 11px; text-align: left; }}
.dp-quick:hover {{ background: #2a2a3e; color: #fff; }}
.dp-quick.dp-clear {{ color: #f44336; margin-top: 8px; }}
.dp-quick.dp-clear:hover {{ background: #2a1515; }}
/* 日历区域 */
.dp-calendar-area {{ padding: 14px; min-width: 330px; }}
.dp-input-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 12px; background: #2a2a3e; border-radius: 8px; padding: 8px 12px; }}
.dp-input-row input {{ background: transparent; border: none; color: #e0e0e0; font-size: 14px; outline: none; width: 110px; text-align: center; }}
.dp-input-row input::placeholder {{ color: #666; }}
.dp-arrow {{ color: #888; font-size: 14px; }}
/* 日历导航 */
.dp-cal-header {{ display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px; }}
.dp-nav-btn {{ background: transparent; border: 1px solid #444; color: #aaa; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 14px; }}
.dp-nav-btn:hover {{ border-color: #667eea; color: #fff; }}
.dp-month-year {{ font-size: 15px; font-weight: 600; color: #e0e0e0; min-width: 120px; text-align: center; }}
/* 星期行 */
.dp-weekdays {{ display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; margin-bottom: 6px; }}
.dp-weekdays span {{ font-size: 12px; color: #888; padding: 4px 0; }}
.dp-weekdays .dp-weekend {{ color: #f44336; }}
/* 日期网格 */
.dp-days-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }}
.dp-day {{ text-align: center; padding: 6px 0; border-radius: 6px; cursor: pointer; font-size: 13px; color: #ccc; }}
.dp-day:hover {{ background: #2a2a3e; }}
.dp-day.other-month {{ color: #444; cursor: default; }}
.dp-day.other-month:hover {{ background: transparent; }}
.dp-day.today {{ font-weight: bold; color: #667eea; }}
.dp-day.in-range {{ background: #252540; color: #667eea; border-radius: 0; }}
.dp-day.range-start {{ background: #667eea; color: #fff; border-radius: 6px 0 0 6px; }}
.dp-day.range-end {{ background: #667eea; color: #fff; border-radius: 0 6px 6px 0; }}
.dp-day.range-single {{ background: #667eea; color: #fff; border-radius: 6px; }}

/* 报告卡片网格 */
.report-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }}
.report-card {{ background: #1a1a2e; border-radius: 12px; padding: 18px; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }}
.report-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2); }}
.card-header {{ display: flex; align-items: center; }}
.card-date-icon {{ font-size: 14px; color: #e0e0e0; white-space: nowrap; }}
.card-pass-rate {{ font-size: 22px; font-weight: bold; margin-left: auto; }}
.card-exec-time {{ font-size: 12px; color: #90caf9; margin-top: 2px; margin-bottom: 8px; }}
.card-stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }}
.stat {{ font-size: 13px; padding: 3px 8px; border-radius: 6px; background: #252540; }}
.stat-pass {{ color: #4CAF50; }}
.stat-fail {{ color: #f44336; }}
.stat-broken {{ color: #ff9800; }}
.stat-skip {{ color: #9e9e9e; }}
.stat-time {{ color: #90caf9; }}
.card-env {{ font-size: 12px; color: #888; margin-bottom: 10px; display: flex; gap: 12px; flex-wrap: wrap; }}
.card-bar {{ height: 4px; border-radius: 2px; background: #333; display: flex; overflow: hidden; }}
.bar-pass {{ background: #4CAF50; transition: width 0.3s; }}
.bar-fail {{ background: #f44336; }}

/* 分页 */
.pagination {{ display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 24px; flex-wrap: wrap; }}
.pagination button {{ background: #2a2a3e; border: 1px solid #444; color: #e0e0e0; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 14px; }}
.pagination button:hover {{ background: #3a3a4e; }}
.pagination button:disabled {{ opacity: 0.4; cursor: default; }}
.pagination .page-info {{ color: #888; font-size: 14px; margin: 0 10px; }}
.pagination .page-size {{ background: #2a2a3e; border: 1px solid #444; color: #e0e0e0; padding: 6px 10px; border-radius: 6px; font-size: 14px; outline: none; }}
.pagination .page-jump {{ display: flex; align-items: center; gap: 4px; margin-left: 10px; }}
.pagination .page-jump input {{ width: 50px; background: #2a2a3e; border: 1px solid #444; color: #e0e0e0; padding: 6px 8px; border-radius: 6px; font-size: 14px; text-align: center; outline: none; }}
.pagination .page-jump input:focus {{ border-color: #667eea; }}
.pagination .page-jump button {{ padding: 6px 10px; font-size: 13px; }}

.footer {{ text-align: center; padding: 30px; color: #555; font-size: 13px; }}

@media (max-width: 768px) {{
    .report-grid {{ grid-template-columns: 1fr; }}
    .summary-bar {{ gap: 20px; }}
    .summary-item .num {{ font-size: 22px; }}
    .toolbar .controls {{ width: 100%; }}
    .toolbar input {{ flex: 1; }}
}}
</style>
</head>
<body>

<div class="header">
    <h1>📊 历史测试报告仪表盘</h1>
    <div class="subtitle" id="headerSubtitle">共 {summary["total_runs"]} 次运行 · {summary["total_cases"]} 个用例 · 最新通过率 {summary["latest_pass_rate"]}%</div>
</div>

<div class="summary-bar">
    <div class="summary-item"><div class="num" style="color:#667eea">{summary["total_runs"]}</div><div class="label">运行次数</div></div>
    <div class="summary-item"><div class="num" style="color:#4CAF50">{summary["total_passed"]}</div><div class="label">通过</div></div>
    <div class="summary-item"><div class="num" style="color:#f44336">{summary["total_failed"]}</div><div class="label">失败</div></div>
    <div class="summary-item"><div class="num" style="color:#ff9800">{summary["total_broken"]}</div><div class="label">异常</div></div>
    <div class="summary-item"><div class="num" style="color:#9e9e9e">{summary["total_skipped"]}</div><div class="label">跳过</div></div>
    <div class="summary-item"><div class="num" style="color:#90caf9">{summary["latest_pass_rate"]}%</div><div class="label">最新通过率</div></div>
</div>

<div class="container">

    <!-- 趋势图 -->
    <div class="chart-section">
        <h2>📈 通过率趋势 <span id="chartInfo" style="font-size:14px;color:#888;font-weight:normal"></span></h2>
        <div class="chart-wrap">
            <canvas id="trendChart"></canvas>
            <div class="chart-tooltip" id="chartTooltip"></div>
        </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
        <h2>📋 历史报告列表 <span id="resultCount" style="font-size:14px;color:#888;font-weight:normal"></span></h2>
        <div class="controls">
            <input type="text" id="searchInput" placeholder="🔍 搜索报告名称..." oninput="onSearch()">
            <select id="statusFilter" onchange="applyFilter()">
                            <option value="all">全部</option>
                            <option value="passed">✅ 通过</option>
                            <option value="failed">❌ 失败</option>
                            <option value="broken">💥 异常</option>
                            <option value="skipped">⏭️ 跳过</option>
                        </select>
                        <div class="date-filter-wrap" onclick="event.stopPropagation()">
                            <span class="date-filter-btn" id="dateFilterBtn" onclick="toggleDatePicker()">📅 日期</span>
                            <div class="date-picker-popup" id="datePickerPopup" onclick="event.stopPropagation()">
                                                            <div class="dp-sidebar">
                                                                <div class="dp-sidebar-title">快捷选择</div>
                                                                <button class="dp-quick" onclick="setQuickDate(1)">最近 1 天</button>
                                                                <button class="dp-quick" onclick="setQuickDate(7)">最近 7 天</button>
                                                                <button class="dp-quick" onclick="setQuickDate(14)">最近 14 天</button>
                                                                <button class="dp-quick" onclick="setQuickDate(30)">最近 30 天</button>
                                                                <button class="dp-quick dp-clear" onclick="clearDateFilter()">清除筛选</button>
                                                            </div>
                                                            <div class="dp-calendar-area">
                                                                <div class="dp-input-row">
                                                                    <input type="text" id="dpStart" placeholder="开始日期" readonly>
                                                                    <span class="dp-arrow">→</span>
                                                                    <input type="text" id="dpEnd" placeholder="结束日期" readonly>
                                                                </div>
                                                                <div class="dp-cal-header">
                                                                    <button class="dp-nav-btn" onclick="dpPrevYear()">«</button>
                                                                    <button class="dp-nav-btn" onclick="dpPrevMonth()">‹</button>
                                                                    <span class="dp-month-year" id="dpMonthYear">2026年7月</span>
                                                                    <button class="dp-nav-btn" onclick="dpNextMonth()">›</button>
                                                                    <button class="dp-nav-btn" onclick="dpNextYear()">»</button>
                                                                </div>
                                                                <div class="dp-weekdays">
                                                                    <span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span class="dp-weekend">日</span>
                                                                </div>
                                                                <div class="dp-days-grid" id="dpDaysGrid"></div>
                                                            </div>
                                                        </div>
                        </div>
            <button onclick="location.reload()">🔄 刷新</button>
        </div>
    </div>

    <!-- 报告卡片网格 -->
    <div class="report-grid" id="reportGrid"></div>

    <!-- 分页 -->
    <div class="pagination" id="pagination">
        <select class="page-size" id="pageSizeSelect" onchange="onPageSizeChange()">
            <option value="5">5条/页</option>
            <option value="10" selected>10条/页</option>
            <option value="20">20条/页</option>
        </select>
        <button id="prevBtn" onclick="goToPage(currentPage - 1)">‹ 上一页</button>
        <span class="page-info" id="pageInfo">第 1 页，共 1 页</span>
        <button id="nextBtn" onclick="goToPage(currentPage + 1)">下一页 ›</button>
        <span class="page-jump">
            <input type="number" id="pageJump" min="1" value="1" onkeydown="if(event.key==='Enter')jumpToPage()">
            <button onclick="jumpToPage()">跳转</button>
        </span>
    </div>
</div>

<div class="footer">
    Auto Test Framework · Allure Dashboard · 每次测试运行后自动更新
</div>

<script>
// ===== 所有报告数据 =====
const ALL_REPORTS = {reports_json};

// ===== 状态变量 =====
let currentPage = 1;
let pageSize = 10;
let statusFilter = 'all';
let dateFilterStart = '';
let dateFilterEnd = '';

// ===== 日期解析 =====
function parseReportDate(str) {{
    if (!str) return null;
    // 支持 "2026-07-15 16:42:07"
    let m = str.match(/(\\d{{4}})[-年](\\d{{1,2}})[-月](\\d{{1,2}})/);
    if (m) return new Date(parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]));
    // 支持 "26-07-15_16-42-00" 或 "26-07-15 16-42-00"
    m = str.match(/^(\\d{{2}})[-]?(\\d{{1,2}})[-]?(\\d{{1,2}})/);
    if (m) return new Date(2000 + parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]));
    return null;
}}

// ===== 日历状态 =====
let calYear = new Date().getFullYear();
let calMonth = new Date().getMonth();
let calSelecting = 'start'; // 'start' or 'end'

// ===== 日期筛选弹窗 =====
function toggleDatePicker() {{
    const popup = document.getElementById('datePickerPopup');
    const btn = document.getElementById('dateFilterBtn');
    const isOpen = !popup.classList.contains('show');
    popup.classList.toggle('show');
    btn.classList.toggle('active', isOpen);
    if (isOpen) {{
        renderCalendar();
    }}
}}

// 点击外部关闭弹窗
document.addEventListener('click', function(e) {{
    const popup = document.getElementById('datePickerPopup');
    const btn = document.getElementById('dateFilterBtn');
    if (popup && popup.classList.contains('show')) {{
        popup.classList.remove('show');
        btn.classList.remove('active');
    }}
}});

// ===== 日历渲染 =====
function renderCalendar() {{
    const grid = document.getElementById('dpDaysGrid');
    const header = document.getElementById('dpMonthYear');
    if (!grid) return;
    header.textContent = calYear + '年' + (calMonth + 1) + '月';

    const firstDay = new Date(calYear, calMonth, 1).getDay(); // 0=Sun
    // 转成周一为一周开始: 0->6, 1->0, 2->1, ...
    const startOffset = firstDay === 0 ? 6 : firstDay - 1;
    const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
    const daysInPrev = new Date(calYear, calMonth, 0).getDate();

    const startDate = new Date(dateFilterStart);
    const endDate = new Date(dateFilterEnd);
    const today = new Date();
    const todayStr = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');

    let html = '';
    // 上个月补齐
    for (let i = startOffset - 1; i >= 0; i--) {{
        html += '<div class="dp-day other-month">' + (daysInPrev - i) + '</div>';
    }}
    // 本月
    for (let d = 1; d <= daysInMonth; d++) {{
        const dateObj = new Date(calYear, calMonth, d);
        const dateStr = calYear + '-' + String(calMonth+1).padStart(2,'0') + '-' + String(d).padStart(2,'0');
        const isToday = dateStr === todayStr;

        let cls = 'dp-day';
        if (isToday) cls += ' today';
        if (dateFilterStart && dateFilterEnd) {{
            const s = new Date(dateFilterStart);
            const e = new Date(dateFilterEnd);
            if (dateObj >= s && dateObj <= e) cls += ' in-range';
            if (dateStr === dateFilterStart) cls += ' range-start';
            if (dateStr === dateFilterEnd) cls += ' range-end';
            if (dateFilterStart === dateFilterEnd && dateStr === dateFilterStart) cls = 'dp-day range-single';
        }}
        html += '<div class="' + cls + '" data-date="' + dateStr + '" onclick="onDayClick(this)">' + d + '</div>';
    }}
    // 下个月补齐
    const totalCells = startOffset + daysInMonth;
    const remaining = (7 - totalCells % 7) % 7;
    for (let i = 1; i <= remaining; i++) {{
        html += '<div class="dp-day other-month">' + i + '</div>';
    }}
    grid.innerHTML = html;
}}

function dpPrevMonth() {{
    calMonth--;
    if (calMonth < 0) {{ calMonth = 11; calYear--; }}
    renderCalendar();
}}

function dpNextMonth() {{
    calMonth++;
    if (calMonth > 11) {{ calMonth = 0; calYear++; }}
    renderCalendar();
}}

function dpPrevYear() {{
    calYear--;
    renderCalendar();
}}

function dpNextYear() {{
    calYear++;
    renderCalendar();
}}

function onDayClick(el) {{
    const dateStr = el.getAttribute('data-date');
    if (!dateStr) return;

    if (calSelecting === 'start' || !document.getElementById('dpStart').value) {{
            document.getElementById('dpStart').value = dateStr;
            document.getElementById('dpEnd').value = '';
            calSelecting = 'end';
            // 防御性：确保弹窗保持打开（防止事件冒泡误关闭）
            if (!document.getElementById('datePickerPopup').classList.contains('show')) {{
                toggleDatePicker();
            }}
    }} else {{
        const s = new Date(document.getElementById('dpStart').value);
        const e = new Date(dateStr);
        if (e < s) {{
            // 如果结束日期小于开始日期，交换
            const oldStart = document.getElementById('dpStart').value;
            document.getElementById('dpStart').value = dateStr;
            document.getElementById('dpEnd').value = oldStart;
        }} else {{
            document.getElementById('dpEnd').value = dateStr;
        }}
        calSelecting = 'start';
        autoApplyDateFilter();
        toggleDatePicker(); // 选择完整范围后关闭弹窗
    }}
    renderCalendar();
}}

function setQuickDate(days) {{
    const now = new Date();
    const end = new Date(now);
    const start = new Date(now);
    start.setDate(start.getDate() - days);

    const fmt = d => d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    document.getElementById('dpStart').value = fmt(start);
    document.getElementById('dpEnd').value = fmt(end);
    calSelecting = 'start';
    autoApplyDateFilter();
    toggleDatePicker(); // 快捷选择完整范围后关闭弹窗
}}

function autoApplyDateFilter() {{
    const s = document.getElementById('dpStart').value;
    const e = document.getElementById('dpEnd').value;
    dateFilterStart = s;
    dateFilterEnd = e;
    // 更新按钮文字
    const btn = document.getElementById('dateFilterBtn');
    if (s && e) {{
        const fmt = d => d.replace(/-/g, '/').slice(5);
        btn.textContent = '📅 ' + fmt(s) + '~' + fmt(e);
    }} else if (s) {{
        btn.textContent = '📅 ' + s.replace(/-/g, '/').slice(5) + '~';
    }} else if (e) {{
        btn.textContent = '📅 ~' + e.replace(/-/g, '/').slice(5);
    }} else {{
        btn.textContent = '📅 日期';
    }}
    currentPage = 1;
    render();
}}

function clearDateFilter() {{
    document.getElementById('dpStart').value = '';
    document.getElementById('dpEnd').value = '';
    dateFilterStart = '';
    dateFilterEnd = '';
    document.getElementById('dateFilterBtn').textContent = '📅 日期';
    calSelecting = 'start';
    currentPage = 1;
    render();
}}

// 点击外部关闭弹窗
document.addEventListener('click', function(e) {{
    const wrap = document.querySelector('.date-filter-wrap');
    const popup = document.getElementById('datePickerPopup');
    if (wrap && !wrap.contains(e.target) && popup && popup.classList.contains('show')) {{
        popup.classList.remove('show');
        document.getElementById('dateFilterBtn').classList.remove('active');
    }}
}});

// ===== 搜索过滤（仅报告名称 + 状态筛选 + 日期筛选） =====
function getFilteredReports() {{
    const q = (document.getElementById('searchInput').value || '').trim().toLowerCase();
    let result = ALL_REPORTS;
    // 名称搜索
    if (q) {{
        result = result.filter(r => {{
            const name = (r._display_time || r.timestamp || '').toLowerCase();
            let qi = 0;
            for (let i = 0; i < name.length && qi < q.length; i++) {{
                if (name[i] === q[qi]) qi++;
            }}
            return qi === q.length;
        }});
    }}
    // 状态筛选
    if (statusFilter !== 'all') {{
        result = result.filter(r => {{
            const s = r.statistic || {{}};
            return (s[statusFilter] || 0) > 0;
        }});
    }}
    // 日期筛选
    if (dateFilterStart) {{
            // 使用本地时间解析，与 parseReportDate 保持一致
            const startMs = new Date(dateFilterStart + 'T00:00:00').getTime();
        result = result.filter(r => {{
            const dt = r.datetime || r.timestamp || '';
            const d = parseReportDate(dt);
            return d && d.getTime() >= startMs;
        }});
    }}
    if (dateFilterEnd) {{
        // 结束日期取当天结束（23:59:59）
        const endMs = new Date(dateFilterEnd + 'T23:59:59').getTime();
        result = result.filter(r => {{
            const dt = r.datetime || r.timestamp || '';
            const d = parseReportDate(dt);
            return d && d.getTime() <= endMs;
        }});
    }}
    return result;
}}

// ===== 执行时间格式化 =====
function formatExecTime(startTime, durationSec) {{
    if (!startTime || !durationSec || durationSec <= 0) return '';
    const parts = startTime.split(':');
    if (parts.length < 2) return '';
    const h = parseInt(parts[0]) || 0;
    const m = parseInt(parts[1]) || 0;
    const s = parseInt(parts[2]) || 0;

    // 计算结束时间
    let totalSec = h * 3600 + m * 60 + s + durationSec;
    const eh = String(Math.floor(totalSec / 3600) % 24).padStart(2, '0');
    const em = String(Math.floor((totalSec % 3600) / 60)).padStart(2, '0');
    const es = String(Math.floor(totalSec % 60)).padStart(2, '0');
    const endTime = eh + ':' + em + ':' + es;

    // 格式化时长
    let durStr;
    if (durationSec >= 60) {{
        const dm = Math.floor(durationSec / 60);
        const ds = Math.floor(durationSec % 60);
        durStr = dm + 'm ' + ds + 's';
    }} else {{
        durStr = durationSec.toFixed(1) + 's';
    }}

    return startTime + ' - ' + endTime + ' (' + durStr + ')';
}}

// ===== 日期格式化 =====
function formatDate(datetimeStr) {{
    if (!datetimeStr) return '';
    // 支持 "2026-07-15 16:42:07" 或 "26-07-15_16-42-00"
    let m = datetimeStr.match(/(\\d{{4}})[-年](\\d{{1,2}})[-月](\\d{{1,2}})/);
    if (m) return m[1] + '/' + m[2].padStart(2,'0') + '/' + m[3].padStart(2,'0');
    m = datetimeStr.match(/^(\\d{{2}})[-]?(\\d{{1,2}})[-]?(\\d{{1,2}})/);
    if (m) {{
        const y = parseInt(m[1]) + 2000;
        return y + '/' + m[2].padStart(2,'0') + '/' + m[3].padStart(2,'0');
    }}
    return datetimeStr;
}}

// ===== 渲染卡片 + 分页 =====
function render() {{
    const filtered = getFilteredReports();
    const totalFiltered = filtered.length;
    const totalPages = Math.max(1, Math.ceil(totalFiltered / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;

    const start = (currentPage - 1) * pageSize;
    const end = Math.min(start + pageSize, totalFiltered);
    const pageData = filtered.slice(start, end);

    // 更新结果显示
    document.getElementById('resultCount').textContent =
        totalFiltered > 0 ? `（共 ${{totalFiltered}} 条，显示 ${{start+1}}-${{end}}）` : '（无匹配结果）';

    // 渲染卡片
    const grid = document.getElementById('reportGrid');
    if (pageData.length === 0) {{
        grid.innerHTML = '<div style="text-align:center;padding:60px;color:#888">暂无匹配的报告</div>';
        updatePagination(0, 0);
        updateChart([]);
        return;
    }}

    let html = '';
    for (const r of pageData) {{
        const stat = r.statistic || {{}};
        const passed = stat.passed || 0;
        const failed = stat.failed || 0;
        const broken = stat.broken || 0;
        const skipped = stat.skipped || 0;
        const pr = r._pass_rate || 0;
        const color = r._color || '#888';
        const dur = r.duration_sec || 0;
        const ts = r.timestamp || '';
        const dt = r._display_time || ts;
        const env = r.environment || {{}};
        const url = env.Base_URL || '';
        const browser = env.Browser || '';
                const startTime = r.start_time || '';
                        const datePart = formatDate(r.datetime || r.timestamp || '');
                        const execTime = formatExecTime(startTime, dur);

                        html += `<div class="report-card" style="border-left:5px solid ${{color}}" data-ts="${{ts}}" onclick="window.open('../allure-reports/${{ts}}/index.html','_blank')">
                                    <div class="card-header">
                                        <span class="card-date-icon">📅${{datePart}}</span>
                                        <span class="card-pass-rate" style="color:${{color}}">${{pr}}%</span>
                                    </div>
                                    ${{execTime ? '<div class="card-exec-time">⏰' + execTime + '</div>' : ''}}
                                    <div class="card-stats">
                <span class="stat stat-pass">✅ ${{passed}}</span>
                <span class="stat stat-fail">❌ ${{failed}}</span>
                <span class="stat stat-broken">💥 ${{broken}}</span>
                <span class="stat stat-skip">⏭️ ${{skipped}}</span>
                <span class="stat stat-time">⏱ ${{dur}}s</span>
            </div>
            <div class="card-env">
                            ${{url ? '<span>🌐 ' + url + '</span>' : ''}}
                            ${{browser ? '<span>🖥 ' + browser + '</span>' : ''}}
                        </div>
                                    <div class="card-bar">
                <div class="bar-pass" style="width:${{pr}}%"></div>
                <div class="bar-fail" style="width:${{Math.max(0, 100 - pr)}}%"></div>
            </div>
        </div>`;
    }}
    grid.innerHTML = html;

    // 更新分页
    updatePagination(currentPage, totalPages);

    // 更新趋势图
    updateChart(filtered);
}}

// ===== 分页控制 =====
function updatePagination(page, total) {{
    document.getElementById('pageInfo').textContent = `第 ${{page}} 页，共 ${{total}} 页`;
    document.getElementById('prevBtn').disabled = page <= 1;
    document.getElementById('nextBtn').disabled = page >= total;
    const jumpInput = document.getElementById('pageJump');
    if (jumpInput) jumpInput.value = page;
}}

function goToPage(page) {{
    const filtered = getFilteredReports();
    const total = Math.max(1, Math.ceil(filtered.length / pageSize));
    if (page < 1 || page > total) return;
    currentPage = page;
    render();
}}

function jumpToPage() {{
    const input = document.getElementById('pageJump');
    const page = parseInt(input.value);
    if (isNaN(page) || page < 1) {{ input.value = 1; return; }}
    goToPage(page);
}}

function onPageSizeChange() {{
    pageSize = parseInt(document.getElementById('pageSizeSelect').value);
    currentPage = 1;
    render();
}}

// ===== 搜索（带防抖） =====
let searchTimer = null;
function onSearch() {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {{
        currentPage = 1;
        render();
    }}, 200);
}}

// ===== 状态筛选 =====
function applyFilter() {{
    statusFilter = document.getElementById('statusFilter').value;
    currentPage = 1;
    render();
}}

// ===== 趋势图（纯 Canvas 实现，无外部依赖） =====
function drawTrendChart(canvasId, allData, labels, values) {{
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    const rect = canvas.parentElement.getBoundingClientRect();
    const W = rect.width;
    const H = 220;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, W, H);

    if (!labels || labels.length === 0 || !values || values.length === 0) {{
        ctx.fillStyle = '#555';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('暂无数据', W/2, H/2);
        return;
    }}

    const pad = {{ top: 20, right: 20, bottom: 40, left: 50 }};
    const chartW = W - pad.left - pad.right;
    const chartH = H - pad.top - pad.bottom;

    // 网格 + y轴标签
    const yTicks = [0, 20, 40, 60, 80, 100];
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.font = '12px sans-serif';
    for (const y of yTicks) {{
        const yPx = pad.top + chartH - (y / 100) * chartH;
        ctx.strokeStyle = '#252540';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pad.left, yPx);
        ctx.lineTo(W - pad.right, yPx);
        ctx.stroke();
        ctx.fillStyle = '#888';
        ctx.fillText(y + '%', pad.left - 6, yPx);
    }}

    // x轴标签（取头尾+中间几个，避免重叠）
    const maxLabels = Math.max(2, Math.floor(chartW / 80));
    const step = Math.max(1, Math.floor(labels.length / maxLabels));
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.font = '10px sans-serif';
    ctx.fillStyle = '#888';
    for (let i = 0; i < labels.length; i += step) {{
        const xPx = pad.left + (i / (labels.length - 1)) * chartW;
        const label = (labels[i] || '').replace('\\\\n', ' ');
        ctx.fillText(label.length > 12 ? label.slice(0, 10) + '..' : label, xPx, H - pad.bottom + 6);
    }}
    const lastIdx = labels.length - 1;
    if (lastIdx % step !== 0) {{
        const xPx = pad.left + (lastIdx / (labels.length - 1)) * chartW;
        const label = (labels[lastIdx] || '').replace('\\\\n', ' ');
        ctx.fillText(label.length > 12 ? label.slice(0, 10) + '..' : label, xPx, H - pad.bottom + 6);
    }}

    // 数据点坐标
    const n = values.length;
    const points = values.map((v, i) => ({{
        x: pad.left + (i / (n - 1)) * chartW,
        y: pad.top + chartH - (Math.min(100, Math.max(0, v)) / 100) * chartH,
        v: v,
        label: labels[i] || '',
        data: allData[i] || null
    }}));

    // 渐变填充
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
    grad.addColorStop(0, 'rgba(102, 126, 234, 0.25)');
    grad.addColorStop(1, 'rgba(102, 126, 234, 0.02)');
    ctx.beginPath();
    ctx.moveTo(points[0].x, pad.top + chartH);
    for (const p of points) ctx.lineTo(p.x, p.y);
    ctx.lineTo(points[n-1].x, pad.top + chartH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // 贝塞尔曲线（Catmull-Rom → Cubic Bezier，C1 连续）
        ctx.beginPath();
        ctx.strokeStyle = '#667eea';
        ctx.lineWidth = 2.5;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';

        if (n === 1) {{
            // 单点：画一个点
            ctx.arc(points[0].x, points[0].y, 4, 0, Math.PI * 2);
            ctx.fillStyle = '#667eea';
            ctx.fill();
        }} else if (n === 2) {{
            // 两点：直接画线
            ctx.moveTo(points[0].x, points[0].y);
            ctx.lineTo(points[1].x, points[1].y);
            ctx.stroke();
        }} else {{
            // 多点：Catmull-Rom → Cubic Bezier，相同值用直线
                        for (let i = 0; i < n - 1; i++) {{
                            const p1 = points[i];
                            const p2 = points[i + 1];

                            if (i === 0) ctx.moveTo(p1.x, p1.y);

                            // 相邻两点通过率相同 → 直线连接
                            if (p1.v === p2.v) {{
                                ctx.lineTo(p2.x, p2.y);
                            }} else {{
                                const p0 = i === 0 ? points[0] : points[i - 1];
                                const p3 = i === n - 2 ? points[n - 1] : points[i + 2];

                                const tension = 0.5;
                                const cp1x = p1.x + (p2.x - p0.x) / 6 * tension;
                                const cp1y = p1.y + (p2.y - p0.y) / 6 * tension;
                                const cp2x = p2.x - (p3.x - p1.x) / 6 * tension;
                                const cp2y = p2.y - (p3.y - p1.y) / 6 * tension;

                                ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
                            }}
                        }}
            ctx.stroke();
        }}

    // 数据点
    for (const p of points) {{
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#667eea';
        ctx.fill();
        ctx.strokeStyle = '#0f0f1a';
        ctx.lineWidth = 2;
        ctx.stroke();
    }}

    // 鼠标悬停浮窗
        const tooltip = document.getElementById('chartTooltip');
        if (!tooltip) return;

    canvas.onmousemove = function(e) {{
        const rect2 = canvas.getBoundingClientRect();
        const mx = e.clientX - rect2.left;
        const my = e.clientY - rect2.top;

        let closest = null;
        let minDist = 20;
        for (const p of points) {{
            const dx = mx - p.x;
            const dy = my - p.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < minDist) {{
                minDist = dist;
                closest = p;
            }}
        }}

        if (closest) {{
            const d = closest.data;
            const stat = d.statistic || {{}};
            const pr = d._pass_rate || 0;
            const dur = d.duration_sec || 0;
            const name = formatDateTime(d._display_time || d.timestamp || '');
            tooltip.style.display = 'block';
            tooltip.style.left = (mx + 15) + 'px';
            tooltip.style.top = (my - 10) + 'px';
            const rateColor = pr >= 90 ? '#4CAF50' : pr === 0 ? '#f44336' : '#FF9800';
                        const datePart = formatDate(d._display_time || d.timestamp || '');
                        const execTime = formatExecTime(d.start_time, dur);
                        tooltip.innerHTML =
                            '<div style="display:flex;align-items:center">' +
                            '<span style="font-size:14px;color:#e0e0e0;white-space:nowrap">📅' + datePart + '</span>' +
                            '<span style="font-size:22px;font-weight:bold;margin-left:auto;color:' + rateColor + '">' + pr + '%</span>' +
                            '</div>' +
                            (execTime ? '<div class="card-exec-time" style="margin-top:2px;margin-bottom:6px">⏰' + execTime + '</div>' : '') +
                            '<div class="card-stats" style="margin-bottom:8px">' +
                            '<span style="color:#4CAF50">✅ ' + (stat.passed||0) + '</span>' +
                            '<span style="color:#f44336">❌ ' + (stat.failed||0) + '</span>' +
                            '<span style="color:#ff9800">💥 ' + (stat.broken||0) + '</span>' +
                            '<span style="color:#9e9e9e">⏭️ ' + (stat.skipped||0) + '</span>' +
                            '<span style="color:#888">⏱ ' + dur + 's</span>' +
                            '</div>' +
                            '<div class="card-bar">' +
                            '<div style="height:100%;background:' + rateColor + ';border-radius:2px;width:' + pr + '%"></div>' +
                            '<div style="height:100%;background:#f44336;border-radius:2px;width:' + Math.max(0, 100 - pr) + '%"></div>' +
                            '</div>';
        }} else {{
            tooltip.style.display = 'none';
        }}
    }};

    canvas.onmouseleave = function() {{
        tooltip.style.display = 'none';
    }};
}}

// ===== 日期时间格式化（年/月/日 时:分:秒） =====
function formatDateTime(str) {{
    if (!str) return '';
    // "2026-07-15 16:42:07" → "2026/07/15 16:42:07"
    var m = str.match(/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}}) (\\d{{2}}:\\d{{2}}:\\d{{2}})$/);
    if (m) return m[1] + '/' + m[2] + '/' + m[3] + ' ' + m[4];
    // "26-07-15_16-42-00" → "2026/07/15 16:42:00"
    m = str.match(/^(\\d{{2}})-(\\d{{2}})-(\\d{{2}})[_ ](\\d{{2}})-(\\d{{2}})-(\\d{{2}})$/);
    if (m) return '20' + m[1] + '/' + m[2] + '/' + m[3] + ' ' + m[4] + ':' + m[5] + ':' + m[6];
    return str;
}}

// ===== 趋势图更新（数据升序排列） =====
function updateChart(filteredData) {{
    const q = (document.getElementById('searchInput').value || '').trim();
    let chartData = filteredData;

    if (!q) {{
        chartData = chartData.slice(0, 30);
    }}

    // 升序排列（左旧右新）
    chartData = chartData.slice().reverse();

    const labels = chartData.map(r => formatDateTime(r._display_time || r.timestamp || '').replace(' ', '\\\\n'));
        const values = chartData.map(r => r._pass_rate || 0);

    document.getElementById('chartInfo').textContent =
        q ? `（搜索过滤：${{chartData.length}} 条）` : `（最近 ${{chartData.length}} 条）`;

    drawTrendChart('trendChart', chartData, labels, values);
}}

// ===== 初始化渲染 =====
render();
</script>
</body>
</html>"""

    return html


def _generate_empty_dashboard(reports_dir: Path):
    """生成空状态仪表盘（尚无历史报告时）"""
    reports_dir.mkdir(parents=True, exist_ok=True)
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>测试报告仪表盘</title>
<style>
body { font-family: sans-serif; background: #0f0f1a; color: #e0e0e0; display: flex; justify-content: center; align-items: center; height: 100vh; }
.empty { text-align: center; }
.empty h1 { font-size: 28px; margin-bottom: 10px; }
.empty p { color: #888; }
</style>
</head>
<body>
<div class="empty">
    <h1>📊 暂无测试报告</h1>
    <p>运行 pytest 后，报告将自动出现在此处</p>
</div>
</body>
</html>"""
    (reports_dir / "index.html").write_text(html, encoding="utf-8")
    (reports_dir / "dashboard-data.json").write_text("{}", encoding="utf-8")
    logger.info("📋 已生成空仪表盘: %s", reports_dir / "index.html")