"""
浏览器管理器模块

封装 Playwright 浏览器创建和销毁逻辑：
- 支持 chromium / firefox / webkit
- 支持 headless / headed 模式
- 自动设置视口大小和超时
- 失败时自动截图

用法：
    from ui.browser import BrowserManager
    browser_mgr = BrowserManager()
    page = browser_mgr.new_page()
    page.goto("http://example.com")
    browser_mgr.close()
"""

from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """
    浏览器管理器

    负责 Playwright 浏览器的生命周期管理。
    使用 with 语句自动释放资源：

        with BrowserManager() as mgr:
            page = mgr.new_page()
            page.goto("http://example.com")
    """

    def __init__(
        self,
        browser_type: Optional[str] = None,
        headless: Optional[bool] = False,
        viewport: Optional[dict] = None,
        timeout: Optional[int] = None,
        channel: str = "chrome",  # 使用系统安装的 Chrome
    ):
        """
        Args:
            browser_type: 浏览器类型（chromium/firefox/webkit），默认使用配置
            headless: 是否无头模式，默认使用配置
            viewport: 视口大小，默认使用配置
            timeout: 超时时间（毫秒），默认使用配置
            channel: Playwright 浏览器渠道，默认使用系统 Chrome
        """
        ui_cfg = settings.ui
        self.browser_type = browser_type or ui_cfg.browser
        self.headless = headless if headless is not None else ui_cfg.headless
        # fullscreen 仅 headed 模式生效（headless 下无窗口，回退到 width×height 视口）
        self.fullscreen = ui_cfg.viewport.fullscreen and not self.headless
        self.viewport = (
            viewport if viewport is not None
            else None if self.fullscreen
            else {"width": ui_cfg.viewport.width, "height": ui_cfg.viewport.height}
        )
        self.timeout = timeout or ui_cfg.timeout
        self.channel = channel
        # slow_mo 仅在 headed（有头）模式下生效，headless 下强制为 0 避免无意义等待
        self.slow_mo = 0 if self.headless else ui_cfg.slow_mo

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    def _launch_browser(self) -> Browser:
        """创建浏览器实例"""
        p = sync_playwright().start()
        self._playwright = p

        browser_type_map = {
            "chromium": p.chromium,
            "firefox": p.firefox,
            "webkit": p.webkit,
        }
        browser_launcher = browser_type_map.get(self.browser_type, p.chromium)

        launch_kwargs = {
            "headless": self.headless,
            "slow_mo": self.slow_mo,  # 操作间延迟，仅 headed 模式生效
        }
        if self.fullscreen:
            launch_kwargs["args"] = ["--start-fullscreen"]

        # 使用系统 Chrome（如果指定了 channel）
        if self.channel and self.browser_type == "chromium":
            launch_kwargs["channel"] = self.channel

        logger.info(
            "启动浏览器: type=%s, headless=%s, channel=%s",
            self.browser_type, self.headless, launch_kwargs.get("channel", "N/A"),
        )

        browser = browser_launcher.launch(**launch_kwargs)
        self._browser = browser
        return browser

    def new_context(self) -> BrowserContext:
        """创建浏览器上下文（相当于一个独立的会话）"""
        if self._browser is None:
            self._launch_browser()

        context = self._browser.new_context(
            viewport=self.viewport,
            ignore_https_errors=True,
        )
        context.set_default_timeout(self.timeout)
        self._context = context
        return context

    def new_page(self) -> "Page":
        """创建新页面"""
        context = self.new_context()
        page = context.new_page()
        logger.info("新页面已创建，viewport=%s", self.viewport)
        return page

    @staticmethod
    def take_screenshot(page: Page, name: str = "screenshot") -> Path:
        """
        页面截图（静态方法，无需实例化 BrowserManager）

        Args:
            page: Playwright Page 对象
            name: 截图文件名（不含路径）

        Returns:
            截图文件路径
        """
        screenshot_dir = settings.project_root / "reports" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        filepath = screenshot_dir / f"{name}.png"
        page.screenshot(path=str(filepath))
        logger.info("截图已保存: %s", filepath)
        return filepath

    def close(self):
        """释放所有浏览器资源"""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("浏览器资源已释放")

    def __enter__(self):
        """支持 with 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出 with 语句时自动释放资源"""
        self.close()