"""
登录功能 UI 测试用例

测试登录页面的各项功能：
- 页面正常加载
- 成功登录流程
- 失败登录流程
- 表单校验
- 记住我功能

使用 Allure 报告标注功能模块。
"""

import allure
import pytest

from ui.pages.login_page import LoginPage


@allure.feature("登录功能")
@allure.story("页面加载")
class TestLoginPageLoad:

    @allure.title("页面正常加载")
    def test_login_page_loaded(self, login_page: LoginPage):
        """验证：登录页面正常加载，关键元素可见"""
        with allure.step("验证页面标题"):
            title = login_page.get_page_title()
            allure.attach(title, name="页面标题", attachment_type=allure.attachment_type.TEXT)

        with allure.step("验证登录表单元素可见"):
            login_page.assert_that.element_visible(
                login_page._username_input, desc="用户名输入框"
            )
            login_page.assert_that.element_visible(
                login_page._password_input, desc="密码输入框"
            )
            login_page.assert_that.element_visible(
                login_page._login_button, desc="登录按钮"
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
class TestLoginFlow:

    @allure.title("成功登录")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_login_success(self, login_page: LoginPage, test_data: dict):
        """验证：正确用户名和密码可以成功登录"""
        with allure.step("获取测试数据"):
            credentials = test_data.get("login", {}).get("valid", {})
            username = credentials.get("username", "admin")
            password = credentials.get("password", "admin123")

        with allure.step("执行登录操作"):
            login_page.login(username, password)

        with allure.step("验证登录成功"):
            login_page.assert_login_success()

    @allure.title("登录失败 - 错误密码")
    def test_login_failed_wrong_password(self, login_page: LoginPage):
        """验证：错误密码登录应显示错误提示"""
        with allure.step("使用错误密码登录"):
            login_page.login("admin", "wrong_password")

        with allure.step("验证登录失败"):
            login_page.assert_login_failed()

    @allure.title("登录失败 - 空用户名")
    def test_login_empty_username(self, login_page: LoginPage):
        """验证：空用户名登录应显示校验提示"""
        with allure.step("使用空用户名登录"):
            login_page.login("", "password123")

        with allure.step("验证登录失败"):
            login_page.assert_login_failed("用户名")

    @allure.title("登录失败 - 空密码")
    def test_login_empty_password(self, login_page: LoginPage):
        """验证：空密码登录应显示校验提示"""
        with allure.step("使用空密码登录"):
            login_page.login("admin", "")

        with allure.step("验证登录失败"):
            login_page.assert_login_failed("密码")


@allure.feature("登录功能")
@allure.story("记住我功能")
class TestRememberMe:

    @allure.title("记住我复选框功能")
    def test_remember_me_checkbox(self, login_page: LoginPage):
        """验证：记住我复选框可勾选"""
        with allure.step("勾选记住我"):
            login_page.locator.find(login_page._remember_checkbox).check()

        with allure.step("验证复选框已选中"):
            checkbox = login_page.locator.find(login_page._remember_checkbox)
            assert checkbox.is_checked(), "记住我复选框应处于选中状态"
            allure.attach("复选框已勾选", name="记住我状态")