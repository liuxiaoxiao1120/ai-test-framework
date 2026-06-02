"""系统首页页面对象。"""

import allure
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage


class HomePage(BasePage):
    """封装系统入口和左侧业务菜单操作。"""

    def __init__(
        self,
        page: Page,
        base_url: str,
        entry_path: str,
        timeout: int = 10000,
    ) -> None:
        super().__init__(page, timeout)
        self.home_url = f"{base_url.rstrip('/')}/{entry_path.lstrip('/')}"

    def _visible_text(self, text: str) -> Locator:
        """优先精确匹配文本，必要时退回包含匹配。"""
        exact_locator = self.page.get_by_text(text, exact=True).first
        try:
            exact_locator.wait_for(state="visible", timeout=self.timeout)
            return exact_locator
        except PlaywrightTimeoutError:
            fallback = self.page.get_by_text(text, exact=False).first
            fallback.wait_for(state="visible", timeout=self.timeout)
            return fallback

    @allure.step("打开系统首页")
    def open_home(self) -> None:
        """打开配置中的系统入口页面。"""
        self.goto(self.home_url)

    @allure.step("进入业务菜单：{parent_menu} -> {child_menu}")
    def goto_module(self, parent_menu: str, child_menu: str) -> None:
        """按菜单文本进入指定业务模块。"""
        self.click(self._visible_text(parent_menu))
        self.click(self._visible_text(child_menu))
        self.wait_for_load()
