"""农村公路 - 科学决策页面对象。"""

from collections.abc import Iterable
from typing import Optional

import allure
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from common.assertion import Assert
from pages.base_page import BasePage


class ScienceDecisionPage(BasePage):
    """封装科学决策页面的查询和导出操作。"""

    SEARCH_INPUT_SELECTORS = (
        "input[placeholder*='请输入']",
        "input[placeholder*='关键字']",
        "input[type='search']",
        "form input",
    )
    RESULT_SELECTORS = (
        "table",
        ".ant-table",
        ".el-table",
        "[class*='table']",
        "[class*='list']",
    )

    def __init__(self, page: Page, timeout: int = 10000) -> None:
        super().__init__(page, timeout)

    def _first_visible(
        self, locators: Iterable[Locator], timeout: int = 1500
    ) -> Optional[Locator]:
        """从候选元素中返回第一个可见元素。"""
        for locator in locators:
            candidate = locator.first
            try:
                candidate.wait_for(state="visible", timeout=timeout)
                return candidate
            except PlaywrightTimeoutError:
                continue
        return None

    def _text_button(self, *names: str) -> Optional[Locator]:
        """按按钮文案查找可见按钮，并兼容非标准按钮标签。"""
        role_locators = [self.page.get_by_role("button", name=name, exact=True) for name in names]
        button = self._first_visible(role_locators)
        if button:
            return button

        text_locators = [self.page.get_by_text(name, exact=True) for name in names]
        return self._first_visible(text_locators)

    def _search_input(self) -> Optional[Locator]:
        """按通用输入框特征查找查询输入框。"""
        return self._first_visible(
            [self.page.locator(selector) for selector in self.SEARCH_INPUT_SELECTORS]
        )

    @allure.step("校验科学决策页面加载完成")
    def assert_page_loaded(self) -> None:
        """校验页面包含科学决策模块文案。"""
        title = self._first_visible(
            [
                self.page.get_by_role("heading", name="科学决策", exact=True),
                self.page.get_by_text("科学决策", exact=True),
                self.page.get_by_text("科学决策", exact=False),
            ],
            timeout=self.timeout,
        )
        Assert.is_true(title is not None, "科学决策页面应展示模块标题")

    @allure.step("执行科学决策查询，关键字：{keyword}")
    def search(self, keyword: str = "") -> None:
        """按关键字执行查询；空关键字用于验证默认条件查询。"""
        if keyword:
            search_input = self._search_input()
            Assert.is_true(search_input is not None, "关键字查询时应存在输入框")
            self.fill(search_input, keyword)

        search_button = self._text_button("查询", "搜索")
        Assert.is_true(search_button is not None, "页面应存在查询或搜索按钮")
        self.click(search_button)
        self.wait_for_load()

    @allure.step("校验查询结果加载完成")
    def assert_result_loaded(self) -> None:
        """等待加载状态结束，并确认页面已返回可展示内容。"""
        loading = self.page.locator(
            ".ant-spin-spinning, .el-loading-mask, [class*='loading']"
        ).first
        try:
            loading.wait_for(state="hidden", timeout=self.timeout)
        except PlaywrightTimeoutError:
            Assert.is_true(False, "查询完成后加载状态应结束")

        result = self._first_visible(
            [self.page.locator(selector) for selector in self.RESULT_SELECTORS]
        )
        if result is not None:
            Assert.is_true(True, "查询结果区域应可见")
            return

        # 部分页面在无数据时不渲染表格，继续校验页面主体和模块标题。
        body_text = self.page.locator("body").inner_text(timeout=self.timeout).strip()
        Assert.not_empty(body_text, "查询完成后页面主体不应为空")
        self.assert_page_loaded()

    @allure.step("校验并操作导出按钮")
    def export(self, click_button: bool = False) -> bool:
        """校验导出按钮可用；按需点击以触发真实导出。"""
        export_button = self._text_button("导出", "导出数据")
        Assert.is_true(export_button is not None, "页面应存在导出按钮")
        Assert.is_true(export_button.is_enabled(), "导出按钮应可点击")
        if click_button:
            self.click(export_button)
        return True
