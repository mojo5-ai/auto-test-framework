"""
登录功能 UI 测试用例

测试登录页面的各项功能：
- 页面正常加载
- 成功登录流程
- 失败登录流程
- 表单校验
- 记住密码功能

使用 Allure 报告标注功能模块。
"""

import allure
import pytest

from ui.pages.login_page import LoginPage
from utils.helpers import load_test_data

# 参数化数据集（从 data/test_login_data.yaml 读取，模块导入期加载）
UI_LOGIN_VALID_CASES = load_test_data("test_login", "ui_login_valid_cases")
UI_LOGIN_INVALID_CASES = load_test_data("test_login", "ui_login_invalid_cases")
UI_LOGIN_BOUNDARY_CASES = load_test_data("test_login", "ui_login_boundary_cases")
UI_LOGIN_RETRY_CASES = load_test_data("test_login", "ui_login_retry_cases")


@allure.feature("登录功能")
@allure.story("页面加载")
@pytest.mark.ui
class TestLoginPageLoad:

    @allure.title("页面正常加载")
    def test_login_page_loaded(self, login_page: LoginPage):
        """验证：登录页面正常加载，关键元素可见"""
        with allure.step("验证页面标题"):
            title = login_page.get_page_title()
            allure.attach(title, name="页面标题", attachment_type=allure.attachment_type.TEXT)

        with allure.step("验证登录表单元素可见"):
            login_page.assert_that.element_visible(
                login_page._resolve(login_page._username_input), desc="用户名输入框"
            )
            login_page.assert_that.element_visible(
                login_page._resolve(login_page._password_input), desc="密码输入框"
            )
            login_page.assert_that.element_visible(
                login_page._resolve(login_page._login_button), desc="登录按钮"
            )

    @allure.title("页面包含忘记密码链接")
    def test_forgot_password_link(self, login_page: LoginPage):
        """验证：页面包含"忘记密码"链接"""
        with allure.step("查找忘记密码链接"):
            login_page.assert_that.element_visible(
                login_page._forgot_password_link, by="text",
                desc="忘记密码链接"
            )


@allure.feature("登录功能")
@allure.story("登录流程")
@pytest.mark.ui
class TestLoginFlow:

    @allure.title("成功登录")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("case", UI_LOGIN_VALID_CASES, ids=lambda c: c["id"])
    def test_login_success(self, login_page: LoginPage, case: dict):
        """验证：正确用户名和密码可以成功登录"""
        allure.dynamic.title(f"成功登录 - {case['id']}")

        with allure.step(f"使用账号 {case['username']} 执行登录"):
            login_page.login(case["username"], case["password"])

        with allure.step("验证登录成功"):
            login_page.assert_login_success()

    @allure.title("登录失败 - 错误密码")
    @pytest.mark.parametrize("case", UI_LOGIN_INVALID_CASES, ids=lambda c: c["id"])
    def test_login_failed_wrong_password(self, login_page: LoginPage, case: dict):
        """验证：错误密码登录应显示错误提示"""
        allure.dynamic.title(f"登录失败 - {case['id']}")

        with allure.step(f"使用账号 {case['username']} 和错误密码登录"):
            login_page.login(case["username"], case["password"])

        with allure.step("验证登录失败"):
            login_page.assert_login_failed(case.get("expected_error"))

    @allure.title("登录失败 - 边界值参数化")
    @pytest.mark.parametrize("case", UI_LOGIN_BOUNDARY_CASES, ids=lambda c: c["id"])
    def test_login_boundary_values(self, login_page: LoginPage, case: dict):
        """参数化验证：空用户名/空密码等边界场景的校验提示"""
        allure.dynamic.title(f"登录边界值 - {case['desc']}")

        with allure.step(f"场景: {case['desc']}"):
            login_page.login(case["username"], case["password"])

        with allure.step("验证校验提示"):
            login_page.assert_login_failed(case.get("expected_error"))


@allure.feature("登录功能")
@allure.story("记住密码功能")
@pytest.mark.ui
class TestRememberMe:

    @allure.title("记住密码复选框功能")
    @pytest.mark.skip(reason="登录页已核实无记住密码复选框（2026-11-18 检查页面 DOM），待开发提供后恢复")
    def test_remember_me_checkbox(self, login_page: LoginPage):
        """验证：记住密码复选框可勾选"""
        with allure.step("勾选记住密码"):
            login_page.locator.find(login_page._resolve(login_page._remember_checkbox)).check()

        with allure.step("验证复选框已选中"):
            checkbox = login_page.locator.find(login_page._resolve(login_page._remember_checkbox))
            assert checkbox.is_checked(), "记住密码复选框应处于选中状态"
            allure.attach("复选框已勾选", name="记住密码状态")


@allure.feature("登录功能")
@allure.story("失败重试")
@pytest.mark.ui
class TestLoginRetry:

    @allure.title("登录失败后修正凭证重新登录成功")
    @pytest.mark.parametrize("case", UI_LOGIN_RETRY_CASES, ids=lambda c: c["id"])
    def test_login_retry_after_failure(self, login_page: LoginPage, case: dict):
        """验证：首次用错误密码登录失败后，修正密码可立即重新登录成功"""
        allure.dynamic.title(f"登录失败后重试 - {case['desc']}")

        with allure.step(f"使用账号 {case['username']} 和错误密码执行首次登录"):
            login_page.login(case["username"], case["wrong_password"])

        with allure.step("验证首次登录失败：出现错误通知且仍停留在登录页"):
            # 文案具体值 [待验证]：后端统一提示，不匹配具体文案，只验通知出现
            login_page.assert_login_failed()
            login_page.assert_on_login_page()

        with allure.step("清空密码框并输入正确密码，再次点击登录"):
            login_page.fill_password(case["password"])
            login_page.click_login()

        with allure.step("验证重新登录成功：已离开登录页且登录表单消失"):
            login_page.assert_left_login_page()
            login_page.assert_login_form_hidden()


if __name__ == "__main__":
    pytest.main(["-v", "test_login.py:TestLoginRetry"])
