"""
UI 测试 fixtures

提供 UI 测试所需的共享 fixture：
- browser: 浏览器管理器
- page: Playwright 页面对象
- login_page: 登录页面对象
"""

import pytest
from playwright.sync_api import Page

from config.settings import settings
from ui.browser import BrowserManager
from ui.pages.login_page import LoginPage


@pytest.fixture(scope="session")
def browser_manager():
    """
    浏览器管理器（会话级）
    整个测试会话只启动一次浏览器
    """
    with BrowserManager() as mgr:
        yield mgr


@pytest.fixture
def page(browser_manager: BrowserManager) -> Page:
    """
    每个测试用例创建独立的页面
    测试结束后自动关闭，保证用例隔离
    """
    page = browser_manager.new_page()
    yield page
    page.close()


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """创建登录页面对象并导航"""
    return LoginPage(page).open()


@pytest.fixture
def test_config() -> dict:
    """UI 测试配置（从全局配置读取）"""
    return {
        "base_url": settings.ui.base_url,
        "timeout": settings.ui.timeout,
        "browser": settings.ui.browser,
    }