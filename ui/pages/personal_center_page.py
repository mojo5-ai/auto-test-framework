"""
个人中心页面对象

封装 account/settings 页面的定位与账号信息断言。
DOM 核实记录：Case2Code/knowledge/dom-knowledge.md「个人中心」（2026-11-18）。
"""

from playwright.sync_api import Page

from ui.pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class PersonalCenterPage(BasePage):
    """个人中心页面对象（account/settings）"""

    PAGE_PATH = "account/settings"

    # ========== 元素定位 ==========
    # antd Descriptions：label「账号」与其 value 为兄弟节点（2026-11-18 核实）
    _account_testid = "[data-testid='account-id']"
    _account_label_xpath = (
        "//span[contains(@class,'ant-descriptions-item-label')][normalize-space()='账号']"
    )
    _account_content_xpath = (
        _account_label_xpath
        + "/following-sibling::span[contains(@class,'ant-descriptions-item-content')]"
    )

    def _account_field(self) -> tuple[str, str]:
        """账号字段定位：data-testid 主选，不存在则回退 XPath（按 label 关联 content）"""
        if self.page.locator(self._account_testid).count() > 0:
            return self._account_testid, "css"
        return self._account_content_xpath, "xpath"

    def assert_opened(self):
        """断言已进入个人中心页面"""
        self.assert_that.url_contains("account/settings")
        logger.info("✅ 已进入个人中心页面")

    def get_account_id(self) -> str:
        """获取页面展示的账号 id（调试/报告附加用）"""
        value, by = self._account_field()
        return self.locator.find(value, by=by).inner_text().strip()

    def assert_account_equals(self, expected_account: str):
        """断言页面展示的账号 id 与预期（登录账号）一致"""
        value, by = self._account_field()
        self.assert_that.text_equals(value, expected_account, by=by, desc="个人中心账号id")
        logger.info("✅ 账号 id 与登录账号一致: %s", expected_account)
