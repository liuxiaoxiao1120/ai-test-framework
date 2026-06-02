"""页面对象基类：封装 Playwright 常用操作。"""

from pathlib import Path
from typing import Optional, Union

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from common.logger import get_logger


LocatorTarget = Union[str, Locator]


class BasePage:
    """所有页面对象的公共父类。"""

    def __init__(self, page: Page, timeout: int = 10000) -> None:
        self.page = page
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)

    def _locator(self, target: LocatorTarget) -> Locator:
        """将选择器或 Locator 统一转换为首个匹配元素。"""
        return self.page.locator(target).first if isinstance(target, str) else target.first

    def goto(self, url: str) -> None:
        """打开指定地址并等待页面基础加载完成。"""
        self.logger.info("打开页面: %s", url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
        self.wait_for_load()

    def click(self, target: LocatorTarget) -> None:
        """等待元素可见后点击。"""
        locator = self._locator(target)
        locator.wait_for(state="visible", timeout=self.timeout)
        locator.click(timeout=self.timeout)

    def fill(self, target: LocatorTarget, value: str) -> None:
        """等待输入框可见后填写内容。"""
        locator = self._locator(target)
        locator.wait_for(state="visible", timeout=self.timeout)
        locator.fill(value, timeout=self.timeout)

    def get_text(self, target: LocatorTarget) -> str:
        """获取元素文本内容。"""
        locator = self._locator(target)
        locator.wait_for(state="visible", timeout=self.timeout)
        return locator.inner_text(timeout=self.timeout).strip()

    def is_visible(self, target: LocatorTarget, timeout: Optional[int] = None) -> bool:
        """判断元素在指定时间内是否可见。"""
        locator = self._locator(target)
        try:
            locator.wait_for(state="visible", timeout=timeout or self.timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def screenshot(self, file_path: Union[str, Path], full_page: bool = True) -> Path:
        """保存页面截图，并返回截图文件路径。"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(path), full_page=full_page)
        self.logger.info("页面截图已保存: %s", path)
        return path

    def wait_for_load(self) -> None:
        """等待 DOM 加载；网络持续请求时不强制依赖 networkidle。"""
        self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
        try:
            self.page.wait_for_load_state("networkidle", timeout=2000)
        except PlaywrightTimeoutError:
            self.logger.info("页面存在持续网络请求，继续执行后续元素等待")
