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
    # 使用 CSS 选择器，字段名表明元素用途
    _username_input = "#username"
    _password_input = "#password"
    _login_button = "#login-btn"
    _error_message = ".error-msg"
    _success_message = ".success-msg"
    _remember_checkbox = "#remember-me"
    _forgot_password_link = "忘记密码"

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
        self.locator.find(self._username_input).fill(username)
        # 输入密码
        self.locator.find(self._password_input).fill(password)
        # 点击登录按钮
        self.locator.find(self._login_button).click()

        # 等待页面响应
        self.wait_for_load()
        return self

    def login_with_remember(self, username: str, password: str) -> "LoginPage":
        """勾选"记住我"后登录"""
        logger.info("登录操作（记住我）: username=%s", username)
        self.locator.find(self._username_input).fill(username)
        self.locator.find(self._password_input).fill(password)
        self.locator.find(self._remember_checkbox).click()
        self.locator.find(self._login_button).click()
        self.wait_for_load()
        return self

    def assert_login_success(self):
        """断言登录成功"""
        self.assert_that.element_visible(
            self._success_message, desc="登录成功提示"
        )
        logger.info("✅ 登录验证成功")

    def assert_login_failed(self, expected_error: str = ""):
        """断言登录失败，显示错误信息"""
        self.assert_that.element_visible(
            self._error_message, desc="错误提示"
        )
        if expected_error:
            self.assert_that.text_contains(
                self._error_message, expected_error, desc="错误提示文本"
            )
        logger.info("✅ 登录失败验证成功")

    def assert_login_button_disabled(self):
        """断言登录按钮为禁用状态"""
        self.assert_that.element_disabled(
            self._login_button, desc="登录按钮"
        )

    def go_to_forgot_password(self):
        """点击"忘记密码"链接"""
        self.locator.find(
            self._forgot_password_link, by="text"
        ).click()
        self.wait_for_load()
        return self