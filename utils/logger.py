"""
日志封装模块

统一管理所有日志输出：
- 控制台实时输出（INFO 级别）
- 文件完整记录（DEBUG 级别）
- 自动创建日志目录
- 支持模块级 logger 独立追踪

用法：
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("操作开始")
    logger.error("操作失败", exc_info=True)
"""

import logging
import sys
from pathlib import Path

from config.settings import settings


def get_logger(name: str = __name__) -> logging.Logger:
    """
    获取日志记录器

    每个模块使用自己的名称获取 logger，便于在日志中追踪来源。
    例如: get_logger("api.client") 会在日志中显示 [api.client]

    Args:
        name: 模块名称，通常传入 __name__

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # --- 控制台 Handler（INFO 级别） ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.logging.level.upper(), logging.INFO))
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # --- 文件 Handler（DEBUG 级别，记录所有细节） ---
    log_path = settings.get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger