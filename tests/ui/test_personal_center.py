"""
个人中心 UI 测试用例

场景：登录成功 → 首页右上角头像 hover 弹出账号菜单 → 进入个人中心 →
验证展示的账号 id 与登录账号一致。

DOM 探查记录：knowledge/dom-knowledge.md「首页右上角」「个人中心」（2026-11-18 核实）。
"""

import allure
import pytest

from ui.pages.home_page import HomePage
from ui.pages.login_page import LoginPage
from ui.pages.personal_center_page import PersonalCenterPage
from utils.helpers import load_test_data

# 参数化数据集（从 data/test_personal_center_data.yaml 读取，模块导入期加载）
UI_PERSONAL_CENTER_CASES = load_test_data("test_personal_center", "ui_personal_center_cases")


@allure.feature("个人中心")
@allure.story("账号信息")
@pytest.mark.ui
class TestPersonalCenter:

    @allure.title("个人中心账号 id 与登录账号一致")
    @pytest.mark.parametrize("case", UI_PERSONAL_CENTER_CASES, ids=lambda c: c["id"])
    def test_account_id_matches_login_user(self, login_page: LoginPage, case: dict):
        """验证：个人中心页面展示的账号 id 与登录使用的账号一致"""
        allure.dynamic.title(f"个人中心账号id校验 - {case['desc']}")

        with allure.step(f"使用账号 {case['username']} 登录并进入首页"):
            login_page.login(case["username"], case["password"])
            home = HomePage(login_page.page)
            home.assert_on_home_page()

        with allure.step("hover 右上角头像，验证账号下拉菜单弹出且含「个人中心」"):
            home.hover_avatar()
            home.assert_account_dropdown_visible()
            home.assert_menu_has_personal_center()

        with allure.step("点击「个人中心」，验证进入个人中心页面"):
            home.click_personal_center()
            personal = PersonalCenterPage(login_page.page)
            personal.assert_opened()

        with allure.step(f"验证页面账号 id 与登录账号 {case['username']} 一致"):
            personal.assert_account_equals(case["username"])
