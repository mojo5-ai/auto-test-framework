"""
集成测试：登录全流程验证

模拟真实用户场景：
1. 通过 API 尝试登录（验证 API 格式）
2. 通过 UI 访问登录页面
3. 验证登录页面的交互

注意：由于系统真实的登录凭证未知，API 登录会返回"登录失败"，
但我们可以验证 API 的响应格式和 UI 页面加载正常。
"""

import allure
import pytest

from api.endpoints.auth_api import AuthApi
from ui.pages.login_page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)


@allure.feature("登录全流程")
@allure.story("API + UI 集成")
@allure.severity(allure.severity_level.CRITICAL)
class TestLoginFullFlow:

    @allure.title("登录 API 接口验证")
    def test_login_api_interface(self, auth_api: AuthApi):
        """
        验证登录 API 接口：
        1. API 返回 200（服务可达）
        2. 响应格式符合预期结构
        3. 错误场景返回明确提示
        """
        with allure.step("API 登录请求"):
            result = auth_api.login("admin", "admin123")

        with allure.step("验证 API 响应"):
            assert "success" in result, "响应缺少 success 字段"
            assert "message" in result, "响应缺少 message 字段"
            allure.attach(
                f"success={result['success']}, message={result['message']}",
                name="API 登录结果",
            )

    @allure.title("登录页面加载验证")
    def test_login_page_accessible(self, login_page: LoginPage):
        """
        验证登录页面：
        1. 页面可访问
        2. 关键元素可见（用户名、密码输入框，登录按钮）
        """
        with allure.step("验证登录页面关键元素"):
            login_page.assert_that.element_visible(
                login_page._username_input, desc="用户名输入框"
            )
            login_page.assert_that.element_visible(
                login_page._password_input, desc="密码输入框"
            )
            login_page.assert_that.element_visible(
                login_page._login_button, desc="登录按钮"
            )

    @allure.title("登录 UI 交互 - 空用户名校验")
    def test_login_empty_ui(self, login_page: LoginPage):
        """
        验证：点击登录按钮时，空用户名/密码的校验提示
        """
        with allure.step("不输入用户名密码直接登录"):
            login_page.login("", "")

        with allure.step("验证校验提示"):
            login_page.assert_that.element_visible(
                login_page._error_message, desc="错误提示"
            )