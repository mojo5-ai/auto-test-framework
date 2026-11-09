"""
认证相关 API 封装

跨境电商精细化管理系统的认证接口封装。

已知 API 端点:
  登录:       POST http://10.200.15.3:10002/auth/auth/login
  登出:       POST http://10.200.15.3:10002/auth/auth/logOut
  用户信息:   GET  http://10.200.15.3:10002/auth/account/findAccountDetail

请求格式:
  {"loginId": "用户名", "password": "密码"}

成功响应格式:
  {"success": true, "data": {"accessToken": "xxx", ...}, "errorCode": null, "errorMsg": null}

失败响应格式:
  {"success": false, "errorCode": 200101, "errorMsg": "登录失败，账号或者密码不正确", "data": null}

用法:
    from api.endpoints.auth_api import AuthApi
    auth = AuthApi()
    result = auth.login("admin", "admin123")
    if result["success"]:
        token = result["token"]
"""

from typing import Optional

from api.client import ApiClient
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthApi:
    """认证 API 封装"""

    LOGIN_URL = "/auth/auth/login"
    LOGOUT_URL = "/auth/auth/logOut"
    USER_INFO_URL = "/auth/account/findAccountDetail"

    def __init__(self, client: Optional[ApiClient] = None):
        """
        Args:
            client: ApiClient 实例，不传则自动创建
        """
        self.client = client or ApiClient()

    def login(self, username: str, password: str) -> dict:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            字典:
            - 成功: {"success": True, "token": "xxx", "raw": 原始响应数据}
            - 失败: {"success": False, "message": "错误信息", "raw": 原始响应数据}
        """
        resp = self.client.post(self.LOGIN_URL, json={
            "loginId": username,
            "password": password,
        })

        try:
            data = resp.json()
        except Exception as e:
            logger.error("登录返回非 JSON: %s", resp.text[:200])
            return {"success": False, "message": f"非 JSON 响应: {e}", "raw": resp.text[:200]}

        if not isinstance(data, dict):
            return {"success": False, "message": "响应格式异常", "raw": str(data)[:200]}

        # API 响应检查
        if data.get("success") is True:
            token = None
            if isinstance(data.get("data"), dict):
                token = data["data"].get("accessToken")
            result = {
                "success": True,
                "token": token,
                "message": data.get("errorMsg", "登录成功"),
                "raw": data,
            }
            logger.info("登录成功, token=%s...", (token[:20] + "...") if token else "None")
            return result

        # 登录失败
        error_msg = data.get("errorMsg", "登录失败")
        error_code = data.get("errorCode", "")
        logger.warning("登录失败 [%s]: %s", error_code, error_msg)
        return {
            "success": False,
            "message": error_msg,
            "code": error_code,
            "raw": data,
        }

    def logout(self) -> dict:
        """用户登出"""
        resp = self.client.post(self.LOGOUT_URL)
        try:
            return resp.json()
        except Exception:
            return {"success": False, "raw": resp.text[:200]}

    def get_user_info(self) -> dict:
        """获取当前用户信息"""
        resp = self.client.get(self.USER_INFO_URL)
        try:
            return resp.json()
        except Exception:
            return {"success": False, "raw": resp.text[:200]}