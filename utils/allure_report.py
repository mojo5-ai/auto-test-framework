"""
Allure 报告生成器

从 allure-results JSON 文件生成 HTML 报告。
无需依赖 Allure CLI（Java），纯 Python 实现。

用法：
    from utils.allure_report import generate_allure_report
    generate_allure_report("reports/allure-results", "reports/allure-reports/25-07-15_14-30-00")
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def generate_allure_report(results_dir: str | Path, output_dir: str | Path) -> Path:
    """
    从 allure-results JSON 文件生成 HTML 报告

    Args:
        results_dir: allure-results 目录路径
        output_dir: 报告输出目录路径

    Returns:
        报告 index.html 的路径
    """
    results_path = Path(results_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 读取所有 result JSON 文件
    test_cases = []
    containers = {}

    for f in sorted(results_path.iterdir()):
        if f.suffix == ".json":
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if "-result.json" in f.name:
                    test_cases.append(data)
                elif "-container.json" in f.name:
                    containers[f.name] = data
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning("跳过无效 JSON 文件 %s: %s", f.name, e)

    # 读取环境信息
    env_info = {}
    env_file = results_path / "environment.properties"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env_info[k.strip()] = v.strip()

    # 统计
    total = len(test_cases)
    passed = sum(1 for t in test_cases if t.get("status") == "passed")
    failed = sum(1 for t in test_cases if t.get("status") in ("failed", "broken"))
    skipped = sum(1 for t in test_cases if t.get("status") == "skipped")
    pass_rate = round(passed / total * 100, 1) if total > 0 else 0

    # 生成测试详情行
    rows = []
    for tc in test_cases:
        name = tc.get("name", "未知")
        status = tc.get("status", "unknown")
        stage = tc.get("stage", "")
        full_name = tc.get("fullName", "")
        # 提取 allure 注解
        labels = tc.get("labels", [])
        feature = next((l["value"] for l in labels if l["name"] == "feature"), "")
        story = next((l["value"] for l in labels if l["name"] == "story"), "")
        severity = next((l["value"] for l in labels if l["name"] == "severity"), "normal")

        status_icon = {"passed": "✅", "failed": "❌", "broken": "💥", "skipped": "⏭️", "unknown": "❓"}
        severity_label = {"blocker": "🔴", "critical": "🔶", "normal": "🔵", "minor": "🟢", "trivial": "⚪"}

        status_badge = {
            "passed": '<span class="badge badge-pass">PASSED</span>',
            "failed": '<span class="badge badge-fail">FAILED</span>',
            "broken": '<span class="badge badge-fail">BROKEN</span>',
            "skipped": '<span class="badge badge-skip">SKIPPED</span>',
            "unknown": '<span class="badge badge-skip">UNKNOWN</span>',
        }

        # 提取 steps
        steps_html = ""
        for step in tc.get("steps", []):
            step_name = step.get("name", "")
            step_status = step.get("status", "")
            steps_html += f'<div class="step">{"✅" if step_status == "passed" else "❌"} {step_name}</div>\n'

        # 提取 attachments
        attachments_html = ""
        for att in tc.get("attachments", []):
            att_name = att.get("name", "")
            att_source = att.get("source", "")
            att_type = att.get("type", "")
            # 尝试读取附件内容
            att_path = results_path / att_source
            if att_path.exists():
                if "png" in att_type or "image" in att_type:
                    import base64
                    img_data = base64.b64encode(att_path.read_bytes()).decode()
                    attachments_html += f'<div class="attachment"><img src="data:image/png;base64,{img_data}" style="max-width:600px"/></div>\n'
                else:
                    attachments_html += f'<div class="attachment"><pre>{att_path.read_text(encoding="utf-8")[:500]}</pre></div>\n'

        # 提取 statusDetails
        status_detail = ""
        message = tc.get("statusDetails", {}).get("message", "")
        trace = tc.get("statusDetails", {}).get("trace", "")
        if message:
            status_detail = f'<div class="error-msg"><strong>错误信息:</strong><pre>{message}</pre></div>'
        if trace:
            status_detail += f'<div class="error-trace"><strong>堆栈:</strong><pre>{trace[:1000]}</pre></div>'

        rows.append(f"""
        <tr class="row-{status}" onclick="toggleDetails('detail-{tc.get("uuid", name)}')">
            <td>{status_badge.get(status, status)}</td>
            <td>{severity_label.get(severity, "⚪")} {severity}</td>
            <td>{feature}</td>
            <td>{story}</td>
            <td>{name}</td>
            <td class="full-name">{full_name}</td>
        </tr>
        <tr class="detail-row" id="detail-{tc.get("uuid", name)}" style="display:none">
            <td colspan="6">
                <div class="detail-content">
                    {steps_html}
                    {attachments_html}
                    {status_detail}
                </div>
            </td>
        </tr>
        """)

    # 生成 HTML
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Allure 测试报告 - {now}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
.header h1 {{ font-size: 28px; margin-bottom: 10px; }}
.header .subtitle {{ font-size: 14px; opacity: 0.9; }}
.summary {{ display: flex; justify-content: center; gap: 30px; padding: 30px; background: white; margin: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.summary-item {{ text-align: center; }}
.summary-item .number {{ font-size: 36px; font-weight: bold; }}
.summary-item .label {{ font-size: 14px; color: #666; margin-top: 5px; }}
.summary-item.total .number {{ color: #333; }}
.summary-item.passed .number {{ color: #4CAF50; }}
.summary-item.failed .number {{ color: #f44336; }}
.summary-item.skipped .number {{ color: #FF9800; }}
.env-info {{ background: white; margin: 0 20px 20px; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.env-info h3 {{ margin-bottom: 10px; color: #667eea; }}
.env-info table {{ width: 100%; border-collapse: collapse; }}
.env-info td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
.env-info td:first-child {{ font-weight: bold; width: 120px; color: #666; }}
table.test-results {{ width: calc(100% - 40px); margin: 0 20px 40px; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
th {{ background: #f8f9fa; padding: 14px 16px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #eee; }}
td {{ padding: 12px 16px; border-bottom: 1px solid #f0f0f0; }}
tr:hover {{ background: #f8f9ff; cursor: pointer; }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
.badge-pass {{ background: #e8f5e9; color: #2e7d32; }}
.badge-fail {{ background: #ffebee; color: #c62828; }}
.badge-skip {{ background: #fff3e0; color: #e65100; }}
.detail-row td {{ background: #fafafa; padding: 0; }}
.detail-content {{ padding: 20px; border-top: 2px solid #667eea; }}
.step {{ padding: 6px 12px; margin: 4px 0; background: #f5f5f5; border-radius: 6px; font-size: 14px; }}
.attachment {{ margin: 10px 0; }}
.attachment pre {{ background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; }}
.error-msg {{ margin: 10px 0; padding: 12px; background: #fff3f3; border-left: 4px solid #f44336; border-radius: 4px; }}
.error-trace {{ margin: 10px 0; padding: 12px; background: #1e1e1e; color: #d4d4d4; border-radius: 6px; font-size: 12px; overflow-x: auto; }}
.full-name {{ font-size: 12px; color: #999; }}
.footer {{ text-align: center; padding: 20px; color: #999; font-size: 13px; }}
</style>
</head>
<body>
<div class="header">
    <h1>📊 Allure 测试报告</h1>
    <div class="subtitle">生成时间: {now} | 环境: {env_info.get('Environment', 'N/A')} | 目标: {env_info.get('Base_URL', 'N/A')}</div>
</div>

<div class="summary">
    <div class="summary-item total">
        <div class="number">{total}</div>
        <div class="label">总计</div>
    </div>
    <div class="summary-item passed">
        <div class="number">{passed}</div>
        <div class="label">通过</div>
    </div>
    <div class="summary-item failed">
        <div class="number">{failed}</div>
        <div class="label">失败</div>
    </div>
    <div class="summary-item skipped">
        <div class="number">{skipped}</div>
        <div class="label">跳过</div>
    </div>
    <div class="summary-item passed">
        <div class="number">{pass_rate}%</div>
        <div class="label">通过率</div>
    </div>
</div>

<div class="env-info">
    <h3>📍 环境信息</h3>
    <table>
"""

    for k, v in env_info.items():
        html += f"        <tr><td>{k}</td><td>{v}</td></tr>\n"

    html += f"""    </table>
</div>

<table class="test-results">
<thead>
<tr>
    <th style="width:100px">状态</th>
    <th style="width:80px">级别</th>
    <th style="width:120px">功能</th>
    <th style="width:120px">场景</th>
    <th>测试名称</th>
    <th style="width:200px">全名</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>

<div class="footer">
    <p>Auto Test Framework | Powered by pytest + Allure</p>
</div>

<script>
function toggleDetails(id) {{
    var el = document.getElementById(id);
    if (el.style.display === 'none' || el.style.display === '') {{
        el.style.display = 'table-row';
    }} else {{
        el.style.display = 'none';
    }}
}}
</script>
</body>
</html>"""

    # 写入 index.html
    index_path = output_path / "index.html"
    index_path.write_text(html, encoding="utf-8")
    logger.info("✅ 报告已生成: %s", index_path)
    return index_path