"""
登录页面对象

示例 Page Object：登录页面
封装登录页面的元素定位和操作流程。

用法：
    from ui.pages.login_page import LoginPage
    login_page = LoginPage(page).open()
    login_page.login("admin", "password123")
    login_page.assert_login_success()
"""

from playwright.sync_api import Page

from ui.pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    """登录页面对象"""

    PAGE_PATH = "login"

    # ========== 元素定位 ==========
    # 优先使用 data-testid（稳定，不受 CSS/文案变更影响），
    # 回退到 CSS id（开发未加 testid 时使用）
    _username_input = "[data-testid='login-username']"
    _password_input = "[data-testid='login-password']"
    _login_button = "[data-testid='login-submit']"
    _error_message = "[data-testid='login-error']"
    _success_message = "[data-testid='login-success']"
    _remember_checkbox = "[data-testid='login-remember']"
    _forgot_password_link = "找回密码"  # 页面真实文案（2026-11-18 核实 DOM）

    # 回退选择器（当开发未加 data-testid 时使用，均已按登录页真实 DOM 核实）
    # 注意：CSS id 选择器必须带 "#"，否则会变成标签选择器永远匹配不到
    _FALLBACK = {
        _username_input: "#loginId",
        _password_input: "#password",
        _login_button: ".ant-btn-primary",           # 登录页唯一主按钮，文本"登 录"
        _error_message: ".ant-notification-notice",  # antd 通知：登录失败提示
        _success_message: ".avatar-content",            # 成功提示元素未知，待有效凭证后核实（暂时使用首页个人中心元素）
        _remember_checkbox: "#remember-me",
    }

    def _resolve(self, selector: str) -> str:
        """
        解析元素选择器：优先用 data-testid，若页面中不存在则回退到 CSS id。

        这样在开发未加 testid 的过渡期，框架仍能正常工作；
        一旦开发补上 testid，自动切到更稳定的定位方式。
        """
        fallback = self._FALLBACK.get(selector)
        if fallback and self.page.locator(selector).count() == 0:
            return fallback
        return selector

    def login(self, username: str, password: str) -> "LoginPage":
        """
        执行登录操作

        Args:
            username: 用户名
            password: 密码

        Returns:
            self，支持链式调用
        """
        logger.info("登录操作: username=%s", username)

        # 输入用户名
        self.locator.find(self._resolve(self._username_input)).fill(username)
        # 输入密码
        self.locator.find(self._resolve(self._password_input)).fill(password)
        # 点击登录按钮
        self.locator.find(self._resolve(self._login_button)).click()

        # 等待页面响应
        self.wait_for_load()
        return self

    def login_with_remember(self, username: str, password: str) -> "LoginPage":
        """勾选"记住密码"后登录"""
        logger.info("登录操作（记住密码）: username=%s", username)  
        self.locator.find(self._resolve(self._username_input)).fill(username)
        self.locator.find(self._resolve(self._password_input)).fill(password)
        self.locator.find(self._resolve(self._remember_checkbox)).click()
        self.locator.find(self._resolve(self._login_button)).click()
        self.wait_for_load()
        return self

    def assert_login_success(self):
        """断言登录成功"""
        self.assert_that.element_visible(
            self._resolve(self._success_message), desc="登录成功提示"
        )
        logger.info("✅ 登录验证成功")

    def assert_login_failed(self, expected_error: str = ""):
        """断言登录失败，显示错误信息"""
        self.assert_that.element_visible(
            self._resolve(self._error_message), desc="错误提示"
        )
        if expected_error:
            self.assert_that.text_contains(
                self._resolve(self._error_message), expected_error, desc="错误提示文本"
            )
        logger.info("✅ 登录失败验证成功")

    def assert_login_button_disabled(self):
        """断言登录按钮为禁用状态"""
        self.assert_that.element_disabled(
            self._resolve(self._login_button), desc="登录按钮"
        )

    def go_to_forgot_password(self):
        """点击"忘记密码"链接"""
        self.locator.find(
            self._forgot_password_link, by="text"
        ).click()
        self.wait_for_load()
        return self