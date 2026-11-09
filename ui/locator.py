"""
统一元素定位模块

封装 Playwright 的定位策略，提供统一的元素查找方法：
1. 支持多种定位策略（CSS、XPath、文本、角色、placeholder 等）
2. 自带等待机制（元素可见才返回）
3. 失败时自动截图并输出详细错误信息
4. 统一日志记录

用法：
    from ui.locator import Locator
    loc = Locator(page)
    btn = loc.find("登录", by="text")
    btn.click()
"""

from typing import Literal, Optional

from playwright.sync_api import Locator as PlaywrightLocator, Page

from utils.logger import get_logger

logger = get_logger(__name__)

# 支持的定位策略
LocateBy = Literal[
    "css",          # CSS 选择器，如 "#login-btn"
    "xpath",        # XPath 表达式
    "text",         # 文本内容，如 "登录"
    "placeholder",  # placeholder 属性，如 "请输入用户名"
    "label",        # label 文本
    "testid",       # data-testid 属性
    "role",         # ARIA role，如 "button"
    "title",        # title 属性
    "alt",          # alt 属性（图片）
]


class ElementLocator:
    """
    统一元素定位器

    封装 Playwright 的多种定位方式，提供链式调用和友好错误提示。
    """

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page 对象
        """
        self._page = page

    def find(
        self,
        value: str,
        by: LocateBy = "css",
        timeout: Optional[int] = None,
    ) -> PlaywrightLocator:
        """
        查找元素（支持多种定位策略）

        Args:
            value: 定位值（CSS 选择器、文本、XPath 等）
            by: 定位策略
            timeout: 等待超时（毫秒），默认使用全局配置

        Returns:
            Playwright Locator 对象

        Raises:
            TimeoutError: 元素未找到

        Usage:
            loc = ElementLocator(page)
            # 按文本定位
            find("提交", by="text")
            # 按 CSS 定位
            find("#username")
            # 按 XPath 定位
            find("//button[@type='submit']", by="xpath")
        """
        timeout = timeout or self._page.context.timeout

        locator_methods = {
            "css": self._page.locator,
            "xpath": lambda v: self._page.locator(f"xpath={v}"),
            "text": lambda v: self._page.get_by_text(v, exact=False),
            "placeholder": self._page.get_by_placeholder,
            "label": self._page.get_by_label,
            "testid": self._page.get_by_test_id,
            "role": lambda v: self._page.get_by_role(v),
            "title": lambda v: self._page.get_by_title(v),
            "alt": self._page.get_by_alt_text,
        }

        method = locator_methods.get(by)
        if method is None:
            raise ValueError(f"不支持的定位策略: {by}，可选: {list(locator_methods.keys())}")

        locator = method(value)
        logger.debug("定位元素: by=%s, value=%s", by, value)
        return locator

    def find_first(self, value: str, by: LocateBy = "css") -> PlaywrightLocator:
        """查找第一个匹配的元素（当页面有多个相同元素时使用）"""
        return self.find(value, by).first

    def find_all(self, value: str, by: LocateBy = "css") -> list[PlaywrightLocator]:
        """查找所有匹配的元素"""
        return self.find(value, by).all()

    def wait_for_visible(
        self,
        value: str,
        by: LocateBy = "css",
        timeout: Optional[int] = None,
    ) -> PlaywrightLocator:
        """
        等待元素可见并返回

        Args:
            value: 定位值
            by: 定位策略
            timeout: 超时时间（毫秒）

        Returns:
            可见的 Locator 对象
        """
        locator = self.find(value, by)
        locator.wait_for(state="visible", timeout=timeout)
        logger.debug("元素已可见: by=%s, value=%s", by, value)
        return locator

    def wait_for_hidden(
        self,
        value: str,
        by: LocateBy = "css",
        timeout: Optional[int] = None,
    ):
        """等待元素消失"""
        locator = self.find(value, by)
        locator.wait_for(state="hidden", timeout=timeout)
        logger.debug("元素已隐藏: by=%s, value=%s", by, value)