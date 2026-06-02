"""农村公路 - 科学决策模块自动化测试。"""

from pathlib import Path
from typing import Any

import allure
import pytest
from playwright.sync_api import Page

from common.yaml_util import YamlUtil
from pages.home_page import HomePage
from pages.road.science_decision_page import ScienceDecisionPage


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_DATA = YamlUtil.load_yaml(PROJECT_ROOT / "data" / "road" / "science_decision.yaml")


@pytest.fixture()
def science_decision_page(
    page: Page, env_config: dict[str, Any], modules_config: dict[str, Any]
) -> ScienceDecisionPage:
    """从首页进入科学决策模块，并返回对应页面对象。"""
    home_page = HomePage(
        page=page,
        base_url=env_config["base_url"],
        entry_path=env_config["entry_path"],
        timeout=int(env_config.get("timeout", 10000)),
    )
    road_module = modules_config["road"]
    home_page.open_home()
    home_page.goto_module(
        parent_menu=road_module["name"],
        child_menu=road_module["menus"]["science_decision"],
    )
    return ScienceDecisionPage(page, timeout=int(env_config.get("timeout", 10000)))


@allure.epic("农村公路")
@allure.feature("科学决策")
class TestScienceDecision:
    """科学决策模块首版冒烟用例。"""

    @allure.story("进入页面")
    @allure.title("成功进入科学决策页面")
    def test_enter_science_decision_page(
        self, science_decision_page: ScienceDecisionPage
    ) -> None:
        """验证菜单跳转后科学决策页面加载成功。"""
        science_decision_page.assert_page_loaded()

    @allure.story("查询")
    @allure.title("科学决策查询：{search_case[name]}")
    @pytest.mark.parametrize(
        "search_case",
        TEST_DATA["search_cases"],
        ids=[case["name"] for case in TEST_DATA["search_cases"]],
    )
    def test_search(
        self,
        science_decision_page: ScienceDecisionPage,
        search_case: dict[str, str],
    ) -> None:
        """验证默认条件和关键字查询可以正常返回页面内容。"""
        science_decision_page.assert_page_loaded()
        science_decision_page.search(keyword=search_case.get("keyword", ""))
        science_decision_page.assert_result_loaded()

    @allure.story("导出")
    @allure.title("导出按钮存在且可点击")
    def test_export_button_available(
        self,
        science_decision_page: ScienceDecisionPage,
        science_decision_data: dict[str, Any],
    ) -> None:
        """验证导出按钮存在且处于可点击状态。"""
        science_decision_page.assert_page_loaded()
        click_button = bool(
            science_decision_data.get("export", {}).get("click_button", False)
        )
        science_decision_page.export(click_button=click_button)
