"""
配置管理模块

基于 pydantic-settings 实现多环境配置加载：
1. 优先读取 config.yaml 中的配置
2. 支持通过环境变量覆盖（前缀 AUTO_TEST_）
3. 支持多环境切换（dev / staging / prod）

用法：
    from config.settings import settings
    settings.api.base_url  # 获取 API 基础地址
"""

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ---------- 子配置模型 ----------

class ApiConfig(BaseModel):
    """API 测试相关配置"""
    base_url: str = "http://10.200.15.3/api/"
    timeout: int = 30
    retry_times: int = 3
    retry_interval: float = 1.0


class ViewportConfig(BaseModel):
    """浏览器视口配置"""
    width: int = 1920
    height: int = 1080


class UiConfig(BaseModel):
    """UI 测试相关配置"""
    base_url: str = "http://10.200.15.3/"
    browser: str = "chromium"
    headless: bool = True
    timeout: int = 30000
    viewport: ViewportConfig = ViewportConfig()


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    file: str = "reports/test.log"


class ReportConfig(BaseModel):
    """报告配置"""
    allure_dir: str = "reports/allure-results"


# ---------- 主配置模型 ----------

class Settings(BaseSettings):
    """全局配置，支持从 YAML 文件和环境变量加载"""

    # 环境名称
    env: str = "dev"

    # 基础地址
    base_url: str = "http://10.200.15.3/"

    # 子配置
    api: ApiConfig = ApiConfig()
    ui: UiConfig = UiConfig()
    logging: LoggingConfig = LoggingConfig()
    report: ReportConfig = ReportConfig()

    # 项目根目录（自动检测）
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    model_config = {"env_prefix": "AUTO_TEST_"}

    @classmethod
    def load_from_yaml(cls, yaml_path: Optional[Path] = None) -> "Settings":
        """
        从 YAML 文件加载配置，YAML 中的值会被环境变量覆盖

        Args:
            yaml_path: YAML 配置文件路径，默认使用 config/config.yaml

        Returns:
            Settings 实例
        """
        if yaml_path is None:
            yaml_path = Path(__file__).resolve().parent / "config.yaml"

        if not yaml_path.exists():
            return cls()

        with open(yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        # 递归合并 YAML 配置到默认值
        return cls(**raw)

    def get_report_dir(self) -> Path:
        """获取 Allure 报告输出目录"""
        return self.project_root / self.report.allure_dir

    def get_log_path(self) -> Path:
        """获取日志文件路径"""
        return self.project_root / self.logging.file


# 全局单例，项目启动时加载一次
settings = Settings.load_from_yaml()