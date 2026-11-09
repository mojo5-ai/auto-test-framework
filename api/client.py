"""
API 基础客户端模块

封装 requests 库，提供统一 HTTP 请求方法：
- 自动拼接 base_url 和 API 路径
- 统一日志记录（请求 URL、参数、响应状态）
- 支持 Token 认证
- 请求超时控制
- 自动重试

用法：
    from api.client import ApiClient
    client = ApiClient()
    resp = client.get("/auth/user/info")
    resp = client.post("/auth/auth/login", json={"username": "admin", "password": "xxx"})
"""

from typing import Any, Optional

import requests

from config.settings import settings
from utils.helpers import retry
from utils.logger import get_logger

logger = get_logger(__name__)


class ApiClient:
    """
    API 客户端

    封装 requests.Session，提供统一的 GET/POST/PUT/DELETE 方法。
    所有请求会自动拼接 base_url 并记录日志。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Args:
            base_url: 基础地址，默认使用配置中的 api.base_url
            token: 认证 Token（Bearer Token）
            timeout: 请求超时秒数，默认使用配置
        """
        self.base_url = base_url or settings.api.base_url
        self.timeout = timeout or settings.api.timeout
        self._session = requests.Session()

        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _build_url(self, endpoint: str) -> str:
        """
        构建完整请求 URL

        Args:
            endpoint: API 端点路径，如 "/auth/auth/login" 或 "auth/auth/login"

        Returns:
            完整 URL
        """
        base = self.base_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base}/{endpoint}"

    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求信息"""
        logger.info("[API] %s %s", method.upper(), url)
        if kwargs.get("params"):
            logger.debug("  params: %s", kwargs["params"])
        if kwargs.get("json"):
            safe_json = kwargs["json"].copy() if isinstance(kwargs["json"], dict) else kwargs["json"]
            if isinstance(safe_json, dict) and "password" in safe_json:
                safe_json["password"] = "******"
            logger.debug("  json: %s", safe_json)

    def _log_response(self, response: requests.Response):
        """记录响应信息"""
        logger.info("[API] %s %s → %d %s",
                     response.request.method,
                     response.url,
                     response.status_code,
                     response.reason)
        try:
            json_body = response.json()
            logger.debug("  response: %s", str(json_body)[:500])
        except Exception:
            logger.debug("  response (non-json): %s", response.text[:200])

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发送 HTTP 请求（内部方法）

        Args:
            method: HTTP 方法
            endpoint: API 端点路径，如 "auth/auth/login"
            **kwargs: 传递给 requests 的参数

        Returns:
            requests.Response 对象
        """
        url = self._build_url(endpoint)
        kwargs.setdefault("timeout", self.timeout)

        self._log_request(method, url, **kwargs)
        response = self._session.request(method, url, **kwargs)
        self._log_response(response)
        return response

    @retry(max_times=3, interval=1.0, exceptions=(requests.exceptions.RequestException,))
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """发送 GET 请求"""
        return self._request("GET", endpoint, **kwargs)

    @retry(max_times=3, interval=1.0, exceptions=(requests.exceptions.RequestException,))
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """发送 POST 请求"""
        return self._request("POST", endpoint, **kwargs)

    @retry(max_times=3, interval=1.0, exceptions=(requests.exceptions.RequestException,))
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """发送 PUT 请求"""
        return self._request("PUT", endpoint, **kwargs)

    @retry(max_times=3, interval=1.0, exceptions=(requests.exceptions.RequestException,))
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """发送 DELETE 请求"""
        return self._request("DELETE", endpoint, **kwargs)

    def close(self):
        """关闭会话，释放连接池"""
        self._session.close()