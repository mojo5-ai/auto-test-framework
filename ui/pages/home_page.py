"""
首页页面对象

封装首页右上角账号管理区域（头像 hover 下拉菜单）的操作与断言。
DOM 核实记录：Case2Code/knowledge/dom-knowledge.md「首页右上角」（2026-11-18）。
"""

from playwright.sync_api import Page

from ui.pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class HomePage(BasePage):
    """首页页面对象（含右上角账号下拉菜单）"""

    PAGE_PATH = "home"

    # ========== 元素定位 ==========
    _avatar = "[data-testid='account-avatar']"
    _dropdown = "[data-testid='account-dropdown']"
    # 菜单项按文本定位：li.ant-dropdown-menu-item 页面上有 3 项，不能作唯一选择器
    _menu_personal_center = "个人中心"

    # 回退选择器（页面无 data-testid 时使用，均已按真实 DOM 核实 2026-11-18）
    # 注意：弹层定位必须用 .ant-dropdown 精确类的子串，不能用 [class*=dropdown]
    # （顶部页签 customsTabs 也是 ant-dropdown-trigger，会误匹配）
    _FALLBACK = {
        _avatar: ".avatar-content",
        _dropdown: ".avatar-dropdown-wrapper",
    }

    def _resolve(self, selector: str) -> str:
        """
        解析元素选择器：优先用 data-testid，若页面中不存在则回退到 CSS。
        与 LoginPage._resolve 同模式。
        """
        fallback = self._FALLBACK.get(selector)
        if fallback and self.page.locator(selector).count() == 0:
            return fallback
        return selector

    def hover_avatar(self) -> "HomePage":
        """hover 右上角头像，触发账号下拉菜单（实测纯 hover 触发，无需点击）"""
        logger.info("hover 右上角头像，触发账号下拉")
        self.locator.find(self._resolve(self._avatar)).hover()
        return self

    def click_personal_center(self) -> "HomePage":
        """点击下拉菜单中的「个人中心」"""
        logger.info("点击菜单项: 个人中心")
        self.locator.find(self._menu_personal_center, by="text").click()
        return self

    def assert_on_home_page(self):
        """断言已进入首页（URL + 右上角头像可见）"""
        self.assert_that.url_contains("home")
        self.assert_that.element_visible(self._resolve(self._avatar), desc="右上角头像")
        logger.info("✅ 已进入首页")

    def assert_account_dropdown_visible(self):
        """断言账号下拉菜单已弹出（hover 后才挂载 DOM，expect 自带轮询等待）"""
        self.assert_that.element_visible(self._resolve(self._dropdown), desc="账号下拉菜单")

    def assert_menu_has_personal_center(self):
        """断言下拉菜单包含「个人中心」项"""
        self.assert_that.element_visible(
            self._menu_personal_center, by="text", desc="菜单项-个人中心"
        )
