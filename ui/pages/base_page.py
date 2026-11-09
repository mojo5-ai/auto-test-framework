"""
基础页面对象模块

所有 Page Object 的基类，提供通用的页面操作方法：
- 统一的元素定位（通过 ElementLocator）
- 统一的断言（通过 Assertions）
- 导航、等待、截图等通用方法

用法：
    class LoginPage(BasePage):
        def login(self, username, password):
            self.locator.find("#username").fill(username)
            ...
"""

from typing import Optional

from playwright.sync_api import Page

from config.settings import settings
from ui.assertions import Assertions
from ui.locator import ElementLocator
from utils.logger import get_logger

logger = get_logger(__name__)


class BasePage:
    """
    页面对象基类

    每个页面对象继承此类，自动获得：
    - self.page: Playwright Page 对象
    - self.locator: 统一元素定位器
    - self.assert_that: 统一断言工具
    - self.open(): 导航到页面 URL
    - self.wait(): 等待页面加载完成
    """

    # 子类覆盖：页面对应的 URL 路径
    PAGE_PATH: str = ""

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page 对象
        """
        self.page = page
        self.locator = ElementLocator(page)
        self.assert_that = Assertions(page)

    @property
    def url(self) -> str:
        """获取当前页面完整 URL"""
        return f"{settings.ui.base_url.rstrip('/')}/{self.PAGE_PATH.lstrip('/')}"

    def open(self, path: Optional[str] = None) -> "BasePage":
        """
        导航到页面

        Args:
            path: 页面路径，不传则使用 PAGE_PATH

        Returns:
            self，支持链式调用
        """
        target = path or self.PAGE_PATH
        full_url = f"{settings.ui.base_url.rstrip('/')}/{target.lstrip('/')}"
        logger.info("导航到: %s", full_url)
        self.page.goto(full_url, wait_until="networkidle")
        return self

    def refresh(self) -> "BasePage":
        """刷新当前页面"""
        logger.info("刷新页面: %s", self.page.url)
        self.page.reload(wait_until="networkidle")
        return self

    def wait_for_load(self, timeout: Optional[int] = None) -> "BasePage":
        """等待页面完全加载"""
        timeout = timeout or settings.ui.timeout
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        return self

    def take_screenshot(self, name: str = "") -> str:
        """
        页面截图

        Args:
            name: 截图文件名（可选）

        Returns:
            截图文件路径
        """
        from ui.browser import BrowserManager
        screenshot_name = name or self.__class__.__name__
        path = BrowserManager().take_screenshot(self.page, screenshot_name)
        return str(path)

    def get_page_title(self) -> str:
        """获取页面标题"""
        return self.page.title()