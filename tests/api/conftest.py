"""
API 测试 fixtures

提供 API 测试所需的共享 fixture：
- api_client: API 客户端实例
- auth_api: 认证 API 封装
- test_data: 测试数据加载
"""

import pytest
import yaml
from pathlib import Path

from api.client import ApiClient
from api.endpoints.auth_api import AuthApi
from config.settings import settings


@pytest.fixture(scope="session")
def api_client() -> ApiClient:
    """
    创建 API 客户端（会话级，所有测试共享）
    复用连接池，提高测试效率
    """
    client = ApiClient()
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_api(api_client: ApiClient) -> AuthApi:
    """创建认证 API 封装对象"""
    return AuthApi(api_client)


@pytest.fixture
def test_data() -> dict:
    """
    加载测试数据文件
    数据存放在 data/test_data.yaml
    """
    data_path = settings.project_root / "data" / "test_data.yaml"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}
