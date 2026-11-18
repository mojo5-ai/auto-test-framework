"""
通用工具函数模块

提供测试中常用的辅助函数，避免重复造轮子。

用法：
    from utils.helpers import retry, wait_for, random_str
"""

import functools
import random
import string
import time
from typing import Any, Callable, Optional, Type

import yaml

from utils.logger import get_logger

logger = get_logger(__name__)


def load_test_data(section: Optional[str] = None) -> Any:
    """
    读取 data/test_data.yaml 中的测试数据

    主要用于 pytest.mark.parametrize：参数化需要在模块导入期拿到数据，
    不能依赖 fixture，因此提供该函数在模块级读取。

    Args:
        section: 顶层数据键，如 "ui_login_boundary_cases"；
                 None 时返回整个数据字典

    Returns:
        指定 section 的数据（通常是 list[dict]），不存在时返回空列表/空字典

    Usage:
        from utils.helpers import load_test_data

        CASES = load_test_data("ui_login_boundary_cases")

        @pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
        def test_xxx(case):
            ...
    """
    # 延迟导入，避免模块级循环依赖
    from config.settings import settings

    data_path = settings.project_root / "data" / "test_data.yaml"
    empty: Any = {} if section is None else []
    if not data_path.exists():
        logger.warning("测试数据文件不存在: %s", data_path)
        return empty

    with open(data_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if section is None:
        return data
    return data.get(section, empty)


def random_str(length: int = 8, prefix: str = "") -> str:
    """
    生成指定长度的随机字符串

    Args:
        length: 字符串长度
        prefix: 可选前缀

    Returns:
        随机字符串，如 "test_Kj3mN9pQ"
    """
    chars = string.ascii_letters + string.digits
    return f"{prefix}_{''.join(random.choices(chars, k=length))}" if prefix else "".join(
        random.choices(chars, k=length)
    )


def random_int(min_val: int = 1000, max_val: int = 9999) -> int:
    """生成随机整数"""
    return random.randint(min_val, max_val)


def retry(
    max_times: int = 3,
    interval: float = 1.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    重试装饰器：当函数抛出指定异常时自动重试

    Args:
        max_times: 最大重试次数
        interval: 重试间隔（秒）
        exceptions: 需要重试的异常类型

    用法:
        @retry(max_times=3, interval=1.0)
        def unstable_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exc = None
            for attempt in range(1, max_times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_times:
                        logger.warning(
                            "%s 第 %d 次尝试失败: %s，%s 秒后重试...",
                            func.__name__, attempt, e, interval,
                        )
                        time.sleep(interval)
            # 保留原始异常类型，便于调用方区分是网络问题还是业务异常
            raise last_exc
        return wrapper
    return decorator


def wait_for(
    condition: Callable[[], Any],
    timeout: float = 10,
    interval: float = 0.5,
    error_msg: str = "等待超时",
) -> Any:
    """
    轮询等待条件成立

    Args:
        condition: 返回真值的可调用对象
        timeout: 超时时间（秒）
        interval: 轮询间隔（秒）
        error_msg: 超时时的错误信息

    Returns:
        条件成立时的返回值

    Raises:
        TimeoutError: 超时后条件仍未成立
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = condition()
        if result:
            return result
        time.sleep(interval)
    raise TimeoutError(f"{error_msg}（{timeout} 秒）")


def extract_json_from_response(response_data: dict, key_path: str) -> Any:
    """
    从嵌套 JSON 中按点号路径提取值

    Args:
        response_data: 响应数据（dict）
        key_path: 点号分隔的路径，如 "data.user.name"

    Returns:
        提取到的值，路径不存在返回 None

    Usage:
        data = {"data": {"user": {"name": "张三"}}}
        extract_json_from_response(data, "data.user.name")  # => "张三"
    """
    keys = key_path.split(".")
    current = response_data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current