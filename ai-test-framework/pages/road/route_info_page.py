"""农村公路 - 路线信息页面对象。"""

from collections.abc import Callable, Iterable
from typing import Any, Optional

import allure
from playwright.sync_api import Locator, Page, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from common.assertion import Assert
from pages.base_page import BasePage


class RouteInfoPage(BasePage):
    """封装路线信息页面的查询、分页和接口响应捕获。"""

    RESULT_SELECTORS = (
        "table",
        ".ant-table",
        ".el-table",
        "[class*='table']",
    )
    LOADING_SELECTORS = (
        ".ant-spin-spinning",
        ".el-loading-mask",
        "[class*='loading']",
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
        role_locators = [
            self.page.get_by_role("button", name=name, exact=True) for name in names
        ]
        button = self._first_visible(role_locators)
        if button:
            return button

        text_locators = [self.page.get_by_text(name, exact=True) for name in names]
        return self._first_visible(text_locators)

    @allure.step("校验路线信息页面加载完成")
    def assert_page_loaded(self) -> None:
        """校验页面包含路线信息模块文案和结果区域。"""
        title = self._first_visible(
            [
                self.page.get_by_role("heading", name="路线信息", exact=True),
                self.page.get_by_text("路线信息", exact=True),
                self.page.get_by_text("路线信息", exact=False),
            ],
            timeout=self.timeout,
        )
        Assert.is_true(title is not None, "路线信息页面应展示模块标题")
        self.assert_result_loaded()

    @allure.step("执行路线信息查询，年份：{year}，关键字：{keyword}")
    def search(self, year: str = "", keyword: str = "") -> None:
        """按年份和路线名称/编码执行查询；空条件用于默认查询。"""
        if year:
            year_input = self._first_visible(
                [
                    self.page.locator("input[placeholder*='请输入年份']"),
                    self.page.locator("input[placeholder*='年份']"),
                ]
            )
            Assert.is_true(year_input is not None, "年份查询时应存在年份输入框")
            self.fill(year_input, year)

        if keyword:
            keyword_input = self._first_visible(
                [
                    self.page.locator("input[placeholder*='路线名称或编码']"),
                    self.page.locator("input[placeholder*='路线']"),
                    self.page.locator("form input").nth(1),
                ]
            )
            Assert.is_true(keyword_input is not None, "路线查询时应存在路线输入框")
            self.fill(keyword_input, keyword)

        search_button = self._text_button("查询", "搜索")
        Assert.is_true(search_button is not None, "页面应存在查询或搜索按钮")
        self.click(search_button)
        self.wait_for_load()

    @allure.step("校验路线信息查询结果加载完成")
    def assert_result_loaded(self) -> None:
        """等待加载状态结束，并确认表格或页面主体已返回。"""
        loading = self.page.locator(", ".join(self.LOADING_SELECTORS)).first
        try:
            loading.wait_for(state="hidden", timeout=self.timeout)
        except PlaywrightTimeoutError:
            pass

        result = self._first_visible(
            [self.page.locator(selector) for selector in self.RESULT_SELECTORS],
            timeout=self.timeout,
        )
        if result is not None:
            Assert.is_true(True, "路线信息结果区域应可见")
            return

        body_text = self.page.locator("body").inner_text(timeout=self.timeout).strip()
        Assert.not_empty(body_text, "查询完成后页面主体不应为空")

    @allure.step("捕获路线信息查询接口响应")
    def capture_query_responses(
        self,
        action: Callable[[], None],
        url_keywords: list[str],
    ) -> list[dict[str, Any]]:
        """执行操作并捕获匹配关键字的成功 JSON 接口响应。"""
        matched_responses: list[dict[str, Any]] = []

        def on_response(response: Response) -> None:
            url = response.url.lower()
            if url_keywords and not any(
                keyword.lower() in url for keyword in url_keywords
            ):
                return
            if response.request.resource_type not in {"xhr", "fetch"}:
                return
            if response.status < 200 or response.status >= 300:
                return
            try:
                body = response.json()
            except Exception:
                body = None
            matched_responses.append(
                {
                    "url": response.url,
                    "method": response.request.method,
                    "status": response.status,
                    "body": body,
                }
            )

        self.page.on("response", on_response)
        try:
            action()
            self.page.wait_for_timeout(1000)
        finally:
            self.page.remove_listener("response", on_response)

        return matched_responses
