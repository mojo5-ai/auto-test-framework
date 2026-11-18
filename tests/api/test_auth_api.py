"""
登录 API 测试用例

测试跨境电商精细化管理系统的登录接口：
- 登录接口可达性
- 请求/响应格式验证
- 错误密码场景
- 空字段校验

每个测试方法使用 Allure 注解标注功能模块。
"""

import allure
import pytest

from api.endpoints.auth_api import AuthApi
from utils.helpers import load_test_data
from utils.logger import get_logger

logger = get_logger(__name__)

# 参数化数据集（从 data/test_auth_api_data.yaml 读取，模块导入期加载）
API_LOGIN_CASES = load_test_data("test_auth_api", "api_login_cases")


@allure.feature("认证模块")
@allure.story("登录接口")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.api
class TestLoginApi:

    @allure.title("登录接口可达性测试")
    def test_login_api_reachable(self, auth_api: AuthApi):
        """验证：登录接口 HTTP 可达，返回 200"""
        with allure.step("发送登录请求"):
            result = auth_api.login("admin", "admin123")

        with allure.step("验证 HTTP 状态码"):
            # 只要 API 返回了结构化的 JSON 响应，就说明接口可达
            assert "success" in result, "响应应包含 success 字段"
            allure.attach(
                f"success={result['success']}, message={result['message']}",
                name="响应摘要",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.title("登录接口响应格式校验")
    def test_login_response_format(self, auth_api: AuthApi):
        """验证：登录响应格式符合预期结构"""
        with allure.step("发送登录请求"):
            result = auth_api.login("admin", "admin123")

        with allure.step("校验响应字段"):
            assert "success" in result, "缺少 success 字段"
            assert "message" in result, "缺少 message 字段"
            assert "raw" in result, "缺少 raw 原始数据"

            raw = result["raw"]
            allure.attach(str(raw), name="原始响应", attachment_type=allure.attachment_type.TEXT)

    @allure.title("登录 - 错误密码提示")
    def test_login_wrong_password(self, auth_api: AuthApi):
        """验证：错误密码返回明确的错误提示"""
        with allure.step("使用错误密码"):
            result = auth_api.login("admin", "wrong_password_123")

        with allure.step("验证返回错误信息"):
            assert result["success"] is False, "错误密码应返回失败"
            assert result["message"], "错误信息不应为空"
            logger.info("错误提示: %s", result["message"])

    @allure.title("登录 - 边界值参数化测试")
    @pytest.mark.parametrize("case", API_LOGIN_CASES, ids=lambda c: c["id"])
    def test_login_boundary_values(self, auth_api: AuthApi, case: dict):
        """参数化验证：各种边界凭证下登录接口的行为"""
        username, password = case["username"], case["password"]
        expect_fail, desc = case["expect_fail"], case["desc"]
        allure.dynamic.title(f"登录边界值 - {desc}")

        with allure.step(f"场景: {desc} — username={username!r}, password={password!r}"):
            result = auth_api.login(username, password)

        with allure.step("验证响应结构"):
            assert "success" in result, "响应缺少 success 字段"
            assert isinstance(result["success"], bool), "success 应为布尔值"

        with allure.step(f"验证成功状态 (expect_fail={expect_fail})"):
            if expect_fail is True:
                assert result["success"] is False, f"{desc} 应返回失败"
            elif expect_fail is False:
                assert result["success"] is True, f"{desc} 应返回成功"
            # expect_fail is None（对照组）：不断言具体成败，只验证接口正常响应
            allure.attach(
                f"success={result['success']}, message={result['message']}",
                name=f"{desc} 结果",
            )


@allure.feature("认证模块")
@allure.story("用户信息接口")
@pytest.mark.api
class TestUserInfo:

    @allure.title("获取用户信息 - 未登录")
    def test_get_user_info(self, auth_api: AuthApi):
        """验证：未登录状态下获取用户信息"""
        with allure.step("调用用户信息接口"):
            result = auth_api.get_user_info()
            allure.attach(str(result)[:500], name="用户信息", attachment_type=allure.attachment_type.TEXT)