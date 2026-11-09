"""
统一断言模块

封装测试中常用的断言方法，提供：
1. 统一的中文错误提示，一目了然
2. 断言失败时自动记录详细上下文
3. 支持软断言（收集所有失败，最后统一报告）

用法：
    from ui.assertions import Assertions
    assert_ = Assertions(page)
    assert_.element_visible("#login-btn")
    assert_.text_equals(".title", "欢迎回来")
"""

from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import Page, expect

from ui.locator import ElementLocator
from utils.logger import get_logger

logger = get_logger(__name__)


class Assertions:
    """
    统一断言工具

    集成 Playwright 的 expect API，提供语义化的断言方法。
    断言失败时自动输出页面 URL 和截图路径（如果配置）。
    """

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page 对象
        """
        self._page = page
        self._locator = ElementLocator(page)

    def _on_failure(self, message: str):
        """断言失败时的回调，输出上下文信息"""
        logger.error("断言失败: %s", message)
        logger.error("  页面 URL: %s", self._page.url)
        # 尝试截图
        try:
            from ui.browser import BrowserManager
            screenshot_path = BrowserManager().take_screenshot(self._page, "assertion_failure")
            logger.info("  失败截图: %s", screenshot_path)
        except Exception:
            pass

    # ========== 元素相关断言 ==========

    def element_visible(self, value: str, by: str = "css", desc: str = "元素"):
        """
        断言元素在页面上可见

        Args:
            value: 定位值
            by: 定位策略
            desc: 元素描述（用于错误提示）
        """
        try:
            locator = self._locator.wait_for_visible(value, by)
            expect(locator).to_be_visible()
            logger.info("✅ %s 可见", desc)
        except AssertionError:
            self._on_failure(f"{desc} 应该可见，但未找到或不可见 (by={by}, value={value})")
            raise

    def element_hidden(self, value: str, by: str = "css", desc: str = "元素"):
        """断言元素隐藏"""
        try:
            locator = self._locator.find(value, by)
            expect(locator).to_be_hidden()
            logger.info("✅ %s 已隐藏", desc)
        except AssertionError:
            self._on_failure(f"{desc} 应该隐藏，但实际可见 (by={by}, value={value})")
            raise

    def element_enabled(self, value: str, by: str = "css", desc: str = "元素"):
        """断言元素可用（未禁用）"""
        try:
            locator = self._locator.find(value, by)
            expect(locator).to_be_enabled()
            logger.info("✅ %s 可用", desc)
        except AssertionError:
            self._on_failure(f"{desc} 应该可用，但实际已禁用 (by={by}, value={value})")
            raise

    def element_disabled(self, value: str, by: str = "css", desc: str = "元素"):
        """断言元素已禁用"""
        try:
            locator = self._locator.find(value, by)
            expect(locator).to_be_disabled()
            logger.info("✅ %s 已禁用", desc)
        except AssertionError:
            self._on_failure(f"{desc} 应该禁用，但实际可用 (by={by}, value={value})")
            raise

    # ========== 文本相关断言 ==========

    def text_equals(self, value: str, expected_text: str, by: str = "css", desc: str = "元素"):
        """断言元素的文本完全等于期望值"""
        try:
            locator = self._locator.find(value, by)
            expect(locator).to_have_text(expected_text)
            logger.info("✅ %s 文本匹配: '%s'", desc, expected_text)
        except AssertionError:
            actual = locator.text_content() or ""
            self._on_failure(f"{desc} 文本不匹配: 期望='{expected_text}', 实际='{actual[:100]}'")
            raise

    def text_contains(self, value: str, expected_text: str, by: str = "css", desc: str = "元素"):
        """断言元素的文本包含期望值"""
        try:
            locator = self._locator.find(value, by)
            expect(locator).to_contain_text(expected_text)
            logger.info("✅ %s 包含文本: '%s'", desc, expected_text)
        except AssertionError:
            actual = locator.text_content() or ""
            self._on_failure(f"{desc} 应包含'{expected_text}'，实际内容: '{actual[:100]}'")
            raise

    # ========== 输入框相关断言 ==========

    def input_has_value(self, value: str, expected_value: str, by: str = "css", desc: str = "输入框"):
        """断言输入框的值等于期望值"""
        try:
            locator = self._locator.find(value, by)
            expect(locator).to_have_value(expected_value)
            logger.info("✅ %s 值匹配: '%s'", desc, expected_value)
        except AssertionError:
            actual = locator.input_value() if by != "text" else ""
            self._on_failure(f"{desc} 值不匹配: 期望='{expected_value}', 实际='{actual}'")
            raise

    # ========== 页面相关断言 ==========

    def url_contains(self, expected_part: str):
        """断言当前 URL 包含特定路径/参数"""
        try:
            expect(self._page).to_have_url(urlpattern=expected_part)
            logger.info("✅ URL 包含: '%s'", expected_part)
        except AssertionError:
            self._on_failure(f"URL 应包含'{expected_part}'，实际 URL: {self._page.url}")
            raise

    def title_equals(self, expected_title: str):
        """断言页面标题等于期望值"""
        try:
            expect(self._page).to_have_title(expected_title)
            logger.info("✅ 页面标题匹配: '%s'", expected_title)
        except AssertionError:
            self._on_failure(f"页面标题不匹配: 期望='{expected_title}', 实际='{self._page.title()}'")
            raise

    # ========== 计数相关断言 ==========

    def elements_count(self, value: str, expected_count: int, by: str = "css", desc: str = "元素"):
        """断言匹配元素的数量"""
        locator = self._locator.find(value, by)
        actual_count = locator.count()
        if actual_count == expected_count:
            logger.info("✅ %s 数量匹配: %d", desc, expected_count)
        else:
            self._on_failure(f"{desc} 数量不匹配: 期望={expected_count}, 实际={actual_count}")
            raise AssertionError(f"{desc} 数量不匹配: 期望={expected_count}, 实际={actual_count}")