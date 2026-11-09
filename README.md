# Auto Test Framework 🧪

跨境电商精细化管理系统自动化测试框架，覆盖 **API 测试 / UI 测试 / 集成测试**，内置 Allure 报告与历史趋势仪表盘。

---

## ✨ 特性

- 🧩 **分层架构** — API / UI / 集成测试模块化组织，职责清晰
- 🔄 **环境切换** — 通过 `--env dev|staging|prod` 一行切换目标环境
- 📊 **Allure 报告** — 自动生成 HTML 报告 + 历史趋势仪表盘
- 📸 **失败截图** — UI 测试失败时自动截图并附加到报告
- 🎲 **数据驱动** — 支持 YAML 数据文件 + Faker 动态生成测试数据
- 🏷️ **标记体系** — `smoke / regression / api / ui / integration` 灵活筛选
- ⚡ **并行执行** — 集成 pytest-xdist，大幅缩短运行时间
- 📝 **全局日志** — 统一日志格式，控制台与文件双输出

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.12 |
| 测试框架 | pytest 8+ |
| API 测试 | requests |
| UI 测试 | Playwright |
| 报告 | Allure |
| 数据校验 | Pydantic v2 |
| 配置 | PyYAML + pydantic-settings |
| 数据生成 | Faker |
| 并行 | pytest-xdist |

---

## 📁 目录结构

```
auto-test-framework/
├── api/                    # API 测试模块
│   ├── client.py           #   HTTP 客户端（重试、超时、鉴权）
│   ├── endpoints/          #   各业务接口封装
│   │   └── auth_api.py
│   └── models/             #   Pydantic 数据模型
│       └── user.py
├── ui/                     # UI 测试模块（Page Object）
│   ├── browser.py          #   Playwright 浏览器管理
│   ├── locator.py          #   定位器封装
│   ├── assertions.py       #   UI 断言库
│   ├── components/         #   公共组件
│   └── pages/              #   页面对象
│       ├── base_page.py
│       └── login_page.py
├── tests/                  # 测试用例
│   ├── api/                #   API 用例
│   ├── ui/                 #   UI 用例
│   └── integration/        #   集成测试
├── config/                 # 配置管理
│   ├── config.yaml         #   全局配置（URL、超时、浏览器）
│   └── settings.py         #   Pydantic Settings 加载器
├── utils/                  # 工具库
│   ├── logger.py           #   日志
│   ├── helpers.py          #   通用函数
│   ├── data_generator.py   #   测试数据生成
│   ├── allure_report.py    #   Allure 辅助
│   └── report_dashboard.py #   仪表盘生成
├── data/                   # 测试数据（YAML）
├── reports/                # 测试产物（自动生成）
│   ├── allure-results/     #   Allure 原始结果
│   ├── allure-reports/     #   Allure HTML 报告（按时间戳）
│   ├── dashboard/          #   历史仪表盘
│   ├── screenshots/        #   UI 失败截图
│   └── test.log            #   运行日志
├── conftest.py             # 全局 pytest fixtures / hooks
├── run.py                  # 🚀 一键运行入口
├── pytest.ini              # pytest 配置
└── requirements.txt        # 依赖清单
```

---

## 🚀 快速开始

### 1. 克隆 & 安装依赖

```bash
git clone https://github.com/mojo5-ai/auto-test-framework.git
cd auto-test-framework

# 推荐使用虚拟环境
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # Linux / macOS

pip install -r requirements.txt
```

### 2. 安装浏览器（UI 测试需要）

```bash
playwright install chromium
```

### 3. 安装 Allure CLI（生成 HTML 报告）

Allure CLI 下载后解压到 `%USERPROFILE%\allure-cli\allure-2.33.0\bin\allure.bat`（Windows）。

> 若无需 HTML 报告，可跳过此步，报告生成会自动降级。

### 4. 修改配置

编辑 `config/config.yaml`，将 `base_url` 改为被测系统地址：

```yaml
base_url: "http://your-system-host/"
api:
  base_url: "http://your-system-host:10002/"
```

### 5. 运行测试

```bash
# 运行全部测试
python run.py

# 只跑 API 测试
python run.py api

# 只跑 UI 测试
python run.py ui

# 只跑冒烟测试
python run.py smoke

# 自定义标记表达式
python run.py -m "api or smoke"

# 切换环境 + 详细日志
python run.py api -v --env staging

# 跑完全部测试并打开仪表盘
python run.py --open

# 仅调试，跳过报告生成
python run.py --no-report
```

也可以直接用 pytest：

```bash
# 全部
pytest tests/

# API 测试 + 并行 4 进程
pytest tests/api/ -n 4

# 冒烟测试
pytest -m smoke

# 指定环境
pytest --env staging
```

---

## 🏷️ 测试标记

在 `pytest.ini` 中预定义了以下标记：

| 标记 | 说明 |
|------|------|
| `api` | API 接口测试 |
| `ui` | UI 端到端测试 |
| `integration` | 跨模块集成测试 |
| `smoke` | 冒烟测试 — 核心功能验证 |
| `regression` | 回归测试 |

在测试函数上使用：

```python
import pytest

@pytest.mark.api
@pytest.mark.smoke
def test_login():
    ...
```

运行时组合筛选：

```bash
pytest -m "api and not smoke"          # API 但非冒烟
pytest -m "smoke or regression"        # 冒烟或回归
```

---

## ⚙️ 配置说明

### config/config.yaml

```yaml
base_url: "http://10.200.15.3/"

api:
  base_url: "http://10.200.15.3:10002/"
  auth_prefix: "auth"
  timeout: 30              # HTTP 超时（秒）
  retry_times: 3           # 失败重试次数
  retry_interval: 1.0      # 重试间隔（秒）

ui:
  base_url: "http://10.200.15.3/"
  browser: "chromium"      # chromium / firefox / webkit
  headless: true           # 是否无头模式
  timeout: 30000           # Playwright 超时（毫秒）
  viewport:
    width: 1920
    height: 1080

logging:
  level: "INFO"
  file: "reports/test.log"

report:
  allure_dir: "reports/allure-results"
```

### 环境变量覆盖

通过 `--env` 或环境变量切换环境：

| 环境 | 用途 |
|------|------|
| `dev` | 本地开发（默认） |
| `staging` | 预发布验证 |
| `prod` | 生产巡检（慎用） |

---

## 📊 查看报告

### Allure HTML 报告

每次运行后自动生成到 `reports/allure-reports/<时间戳>/`，双击 `index.html` 即可。

### 历史仪表盘

`reports/dashboard/index.html` 聚合最近 N 次运行结果，展示通过率、趋势、失败用例。

---

## 📝 编写新测试

### API 测试示例

```python
# tests/api/test_auth_api.py
import pytest
from api.endpoints.auth_api import AuthAPI

@pytest.mark.api
class TestAuth:
    def test_login_success(self, auth_api: AuthAPI):
        resp = auth_api.login("admin", "123456")
        assert resp.status_code == 200
        assert "token" in resp.json()
```

### UI 测试示例（Page Object）

```python
# tests/ui/test_login.py
import pytest

@pytest.mark.ui
class TestLoginPage:
    def test_login_page_loaded(self, login_page):
        login_page.goto()
        assert login_page.is_loaded()

    def test_login_empty_password(self, login_page):
        login_page.goto()
        login_page.login("admin", "")
        assert login_page.error_text_visible()
```

---

## 🔐 安全注意

- 禁止将真实的账号密码、API Token 写入测试代码或配置文件
- 敏感信息统一从环境变量读取，配置文件中仅放占位符
- `.gitignore` 已覆盖 `__pycache__/`、`.pytest_cache/`、`node_modules/`、`allure-reports/results/`、`.idea/` 等

---

## 📄 License

MIT
