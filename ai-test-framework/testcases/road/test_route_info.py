"""农村公路 - 路线信息模块自动化测试。"""

from pathlib import Path
from typing import Any

import allure
import pytest
from playwright.sync_api import Page

from common.assertion import Assert
from common.yaml_util import YamlUtil
from pages.home_page import HomePage
from pages.road.route_info_page import RouteInfoPage


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_DATA = YamlUtil.load_yaml(PROJECT_ROOT / "data" / "road" / "route_info.yaml")


@pytest.fixture(scope="session")
def route_info_data() -> dict[str, Any]:
    """读取路线信息模块测试数据。"""
    return TEST_DATA


@pytest.fixture()
def route_info_page(
    page: Page, env_config: dict[str, Any], modules_config: dict[str, Any]
) -> RouteInfoPage:
    """从首页进入路线信息模块，并返回对应页面对象。"""
    home_page = HomePage(
        page=page,
        base_url=env_config["base_url"],
        entry_path=env_config["entry_path"],
        timeout=int(env_config.get("timeout", 10000)),
    )
    home_page.open_home()
    home_page.goto_menu_path(modules_config["road"]["menus"]["route_info"])
    return RouteInfoPage(page, timeout=int(env_config.get("timeout", 10000)))


@allure.epic("农村公路")
@allure.feature("路线信息")
class TestRouteInfo:
    """路线信息模块冒烟和查询用例。"""

    @allure.story("进入页面")
    @allure.title("成功进入路线信息页面")
    def test_enter_route_info_page(self, route_info_page: RouteInfoPage) -> None:
        """验证菜单跳转后路线信息页面加载成功。"""
        route_info_page.assert_page_loaded()

    @allure.story("查询")
    @allure.title("路线信息查询：{search_case[name]}")
    @pytest.mark.parametrize(
        "search_case",
        TEST_DATA["search_cases"],
        ids=[case["name"] for case in TEST_DATA["search_cases"]],
    )
    def test_search(
        self,
        route_info_page: RouteInfoPage,
        route_info_data: dict[str, Any],
        search_case: dict[str, str],
    ) -> None:
        """验证默认条件和路线关键字查询可以正常返回页面内容。"""
        route_info_page.assert_page_loaded()
        capture_config = route_info_data.get("api_capture", {})
        responses = route_info_page.capture_query_responses(
            lambda: route_info_page.search(
                year=search_case.get("year", ""),
                keyword=search_case.get("keyword", ""),
            ),
            url_keywords=capture_config.get("url_keywords", []),
        )
        route_info_page.assert_result_loaded()

        if bool(capture_config.get("required", False)):
            Assert.is_true(bool(responses), "查询时应捕获到路线信息接口响应")
