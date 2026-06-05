"""Pytest 全局配置：统一管理环境、浏览器、页面和失败截图。"""

import json
import os
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from common.api_client import ApiClient
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
    auth_config = current_env.setdefault("auth", {})
    if os.getenv("AUTH_STORAGE"):
        auth_config["storage"] = os.environ["AUTH_STORAGE"]
    if os.getenv("AUTH_STORAGE_KEY"):
        auth_config["storage_key"] = os.environ["AUTH_STORAGE_KEY"]
    return current_env


@pytest.fixture(scope="session")
def modules_config() -> dict[str, Any]:
    """读取业务模块菜单配置。"""
    return YamlUtil.load_yaml(CONFIG_DIR / "modules.yaml")


@pytest.fixture(scope="session")
def science_decision_data() -> dict[str, Any]:
    """读取科学决策模块测试数据。"""
    return YamlUtil.load_yaml(DATA_DIR / "road" / "science_decision.yaml")


def _build_url(base_url: str, path: str) -> str:
    """拼接基础地址和 hash 路由路径。"""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _extract_json_path(data: Any, json_path: str) -> Optional[str]:
    """按 data.token 这类路径从接口响应 JSON 中取值。"""
    current = data
    for part in json_path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return None
            current = current[index]
        else:
            return None

        if current is None:
            return None
    return str(current)


def _first_visible(page: Page, selectors: list[str], timeout: int) -> Optional[Any]:
    """返回第一个可见元素，用于兼容不同登录页控件写法。"""
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return locator
        except PlaywrightTimeoutError:
            continue
    return None


def _login_by_account(context: BrowserContext, env_config: dict[str, Any]) -> None:
    """使用登录页账号密码完成鉴权；密码允许为空。"""
    auth_config = env_config.get("auth", {})
    login_config = auth_config.get("login", {})
    login_path = login_config.get("path")
    username_env = login_config.get("username_env", "LOGIN_USERNAME")
    password_env = login_config.get("password_env", "LOGIN_PASSWORD")
    username = os.getenv(username_env) or login_config.get("username")
    password = os.getenv(password_env)
    if password is None:
        password = str(login_config.get("password_default", ""))

    if not login_path or not username:
        raise pytest.UsageError(
            "未检测到 ACCESS_TOKEN，也未检测到登录账号；"
            f"请设置 {username_env}，密码为空时可不设置 {password_env}"
        )

    timeout = int(env_config.get("timeout", 10000))
    login_url = _build_url(env_config["base_url"], login_path)
    login_page = context.new_page()
    login_page.set_default_timeout(timeout)
    login_page.set_default_navigation_timeout(timeout)
    try:
        login_page.goto(login_url, wait_until="domcontentloaded", timeout=timeout)
        username_input = _first_visible(
            login_page,
            [
                "input[name='userName']",
                "input[name='username']",
                "input[placeholder*='账号']",
                "input[placeholder*='用户']",
                "input[type='text']",
            ],
            timeout,
        )
        if username_input is None:
            raise pytest.UsageError("登录页未找到账号输入框")
        username_input.fill(username, timeout=timeout)

        password_input = _first_visible(
            login_page,
            [
                "input[name='password']",
                "input[type='password']",
                "input[placeholder*='密码']",
            ],
            timeout,
        )
        if password_input is not None:
            password_input.fill(password, timeout=timeout)

        login_button = _first_visible(
            login_page,
            [
                "button:has-text('登录')",
                "[role='button']:has-text('登录')",
                "text=登录",
            ],
            timeout,
        )
        if login_button is None:
            raise pytest.UsageError("登录页未找到登录按钮")
        login_button.click(timeout=timeout)
        login_page.wait_for_load_state("domcontentloaded", timeout=timeout)
        try:
            login_page.wait_for_url(lambda url: "Login" not in url, timeout=timeout)
        except Exception:
            login_page.wait_for_timeout(1000)
    finally:
        login_page.close()


@pytest.fixture(scope="session")
def access_token() -> Optional[str]:
    """从环境变量读取令牌；未提供时允许走登录页鉴权。"""
    return os.getenv("ACCESS_TOKEN")


@pytest.fixture(scope="session")
def api_config(env_config: dict[str, Any]) -> dict[str, Any]:
    """读取接口测试配置。"""
    api = env_config.get("api", {})
    return api if isinstance(api, dict) else {}


@pytest.fixture(scope="session")
def api_base_url(env_config: dict[str, Any], api_config: dict[str, Any]) -> str:
    """接口基础地址，默认复用当前环境 base_url。"""
    base_url = os.getenv("API_BASE_URL") or api_config.get("base_url")
    base_url = base_url or env_config.get("base_url")
    if not base_url:
        raise pytest.UsageError("未配置接口基础地址，请设置 API_BASE_URL 或 api.base_url")
    return str(base_url)


@pytest.fixture(scope="session")
def api_client(env_config: dict[str, Any], api_base_url: str) -> ApiClient:
    """不带默认鉴权头的接口客户端。"""
    timeout = int(env_config.get("timeout", 10000))
    return ApiClient(api_base_url, timeout=timeout)


@pytest.fixture(scope="session")
def api_token(
    env_config: dict[str, Any], api_config: dict[str, Any], api_base_url: str
) -> Optional[str]:
    """优先读取环境变量 token；没有时按配置调用登录接口获取。"""
    auth_config = api_config.get("auth", {})
    if not isinstance(auth_config, dict):
        auth_config = {}

    token_env = str(auth_config.get("token_env", "ACCESS_TOKEN"))
    token = os.getenv(token_env) or os.getenv("ACCESS_TOKEN")
    if token:
        return token

    login_config = auth_config.get("login", {})
    if not isinstance(login_config, dict):
        login_config = {}

    login_path = str(os.getenv("API_LOGIN_PATH") or login_config.get("path") or "")
    if not login_path:
        return None

    username_env = str(login_config.get("username_env", "LOGIN_USERNAME"))
    password_env = str(login_config.get("password_env", "LOGIN_PASSWORD"))
    username = os.getenv(username_env) or login_config.get("username")
    password = os.getenv(password_env)
    if password is None:
        password = str(login_config.get("password_default", ""))
    if not username:
        raise pytest.UsageError(f"接口登录缺少账号，请设置 {username_env}")

    username_field = str(login_config.get("username_field", "userName"))
    password_field = str(login_config.get("password_field", "password"))
    method = str(login_config.get("method", "POST")).upper()
    payload = {username_field: username, password_field: password}

    timeout = int(env_config.get("timeout", 10000))
    login_client = ApiClient(api_base_url, timeout=timeout)
    response = login_client.request(method, login_path, json=payload)
    try:
        response.raise_for_status()
    except Exception as error:
        raise pytest.UsageError(f"接口登录失败: {response.status_code}") from error

    token_json_path = str(login_config.get("token_json_path", "data.access_token"))
    found_token = _extract_json_path(response.json(), token_json_path)
    if not found_token:
        raise pytest.UsageError(
            f"接口登录响应中未找到 token，请检查 token_json_path: {token_json_path}"
        )
    return found_token


@pytest.fixture(scope="session")
def auth_headers(api_config: dict[str, Any], api_token: Optional[str]) -> dict[str, str]:
    """接口鉴权请求头。"""
    if not api_token:
        pytest.skip("未提供 ACCESS_TOKEN，也未配置 api.auth.login.path，跳过需登录接口")

    auth_config = api_config.get("auth", {})
    if not isinstance(auth_config, dict):
        auth_config = {}
    header_name = str(auth_config.get("header_name", "Authorization"))
    header_prefix = str(auth_config.get("header_prefix", "Bearer")).strip()
    header_value = f"{header_prefix} {api_token}" if header_prefix else api_token
    return {header_name: header_value}


@pytest.fixture(scope="session")
def auth_api_client(
    env_config: dict[str, Any], api_base_url: str, auth_headers: dict[str, str]
) -> ApiClient:
    """默认带鉴权头的接口客户端。"""
    timeout = int(env_config.get("timeout", 10000))
    return ApiClient(api_base_url, timeout=timeout, default_headers=auth_headers)


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
    browser: Browser, env_config: dict[str, Any], access_token: Optional[str]
) -> Generator[BrowserContext, None, None]:
    """创建浏览器上下文，并完成令牌注入或登录页鉴权。"""
    viewport = env_config.get("viewport", {"width": 1440, "height": 900})
    context = browser.new_context(viewport=viewport)

    auth_config = env_config.get("auth", {})
    storage = auth_config.get("storage", "localStorage")
    storage_key = auth_config.get("storage_key", "access_token")
    if storage not in {"localStorage", "sessionStorage"}:
        raise pytest.UsageError(f"不支持的令牌存储类型: {storage}")

    try:
        if access_token:
            init_script = (
                "try { "
                f"window.{storage}.setItem("
                f"{json.dumps(storage_key)}, {json.dumps(access_token)});"
                " } catch (error) {}"
            )
            context.add_init_script(script=init_script)
        else:
            _login_by_account(context, env_config)
        yield context
    finally:
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
