"""Pytest 全局配置：统一管理环境、浏览器、页面和失败截图。"""

import json
import os
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from common.yaml_util import YamlUtil


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"


def pytest_addoption(parser: pytest.Parser) -> None:
    """注册环境切换参数。"""
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="运行环境，可选 test、uat、prod；默认读取 APP_ENV 或 env.yaml",
    )


@pytest.fixture(scope="session")
def env_config(request: pytest.FixtureRequest) -> dict[str, Any]:
    """加载当前运行环境配置，并支持 BASE_URL 临时覆盖。"""
    config = YamlUtil.load_yaml(CONFIG_DIR / "env.yaml")
    env_name = request.config.getoption("--env") or os.getenv("APP_ENV")
    env_name = env_name or config.get("default_env", "test")

    environments = config.get("environments", {})
    if env_name not in environments:
        raise pytest.UsageError(
            f"不支持的运行环境: {env_name}，可选值: {', '.join(environments)}"
        )

    current_env = deepcopy(environments[env_name])
    current_env["name"] = env_name
    if os.getenv("BASE_URL"):
        current_env["base_url"] = os.environ["BASE_URL"]
    return current_env


@pytest.fixture(scope="session")
def modules_config() -> dict[str, Any]:
    """读取业务模块菜单配置。"""
    return YamlUtil.load_yaml(CONFIG_DIR / "modules.yaml")


@pytest.fixture(scope="session")
def science_decision_data() -> dict[str, Any]:
    """读取科学决策模块测试数据。"""
    return YamlUtil.load_yaml(DATA_DIR / "road" / "science_decision.yaml")


@pytest.fixture(scope="session")
def access_token() -> str:
    """仅从环境变量读取令牌，禁止在仓库中保存敏感信息。"""
    token = os.getenv("ACCESS_TOKEN")
    if not token:
        raise pytest.UsageError("未检测到 ACCESS_TOKEN，请先设置环境变量")
    return token


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    """启动并回收 Playwright 运行实例。"""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(
    playwright_instance: Playwright, env_config: dict[str, Any]
) -> Generator[Browser, None, None]:
    """按环境配置启动浏览器。"""
    browser_name = env_config.get("browser", "chromium")
    browser_type = getattr(playwright_instance, browser_name, None)
    if browser_type is None:
        raise pytest.UsageError(f"不支持的浏览器类型: {browser_name}")

    browser_instance = browser_type.launch(
        headless=bool(env_config.get("headless", True)),
        slow_mo=int(env_config.get("slow_mo", 0)),
    )
    yield browser_instance
    browser_instance.close()


@pytest.fixture()
def browser_context(
    browser: Browser, env_config: dict[str, Any], access_token: str
) -> Generator[BrowserContext, None, None]:
    """创建浏览器上下文，并在页面脚本执行前注入访问令牌。"""
    viewport = env_config.get("viewport", {"width": 1440, "height": 900})
    context = browser.new_context(viewport=viewport)

    auth_config = env_config.get("auth", {})
    storage = auth_config.get("storage", "localStorage")
    storage_key = auth_config.get("storage_key", "access_token")
    if storage not in {"localStorage", "sessionStorage"}:
        raise pytest.UsageError(f"不支持的令牌存储类型: {storage}")

    init_script = (
        "try { "
        f"window.{storage}.setItem("
        f"{json.dumps(storage_key)}, {json.dumps(access_token)});"
        " } catch (error) {}"
    )
    context.add_init_script(script=init_script)
    yield context
    context.close()


@pytest.fixture()
def page(
    request: pytest.FixtureRequest,
    browser_context: BrowserContext,
    env_config: dict[str, Any],
) -> Generator[Page, None, None]:
    """为每条用例创建独立页面，避免用例状态相互污染。"""
    current_page = browser_context.new_page()
    timeout = int(env_config.get("timeout", 10000))
    current_page.set_default_timeout(timeout)
    current_page.set_default_navigation_timeout(timeout)
    request.node._playwright_page = current_page
    yield current_page
    current_page.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[Any]
) -> Generator[None, None, None]:
    """在用例执行失败时自动截图，并附加到 Allure 结果。"""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or not report.failed:
        return

    current_page = getattr(item, "_playwright_page", None)
    if current_page is None or current_page.is_closed():
        return

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", item.nodeid)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    screenshot_path = SCREENSHOT_DIR / f"{safe_name}_{timestamp}.png"
    current_page.screenshot(path=str(screenshot_path), full_page=True)
    allure.attach.file(
        str(screenshot_path),
        name=f"失败截图-{item.name}",
        attachment_type=allure.attachment_type.PNG,
    )
