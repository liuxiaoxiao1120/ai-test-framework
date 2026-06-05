"""Minimal web test platform for running local pytest cases."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
CONFIG_FILE = RUNTIME_DIR / "config.json"
LEGACY_DEFAULT_CASE_PATH = "testcases/road/test_route_info.py"

DEFAULT_CONFIG: dict[str, Any] = {
    "base_url": "http://10.6.20.233:8891",
    "api_base_url": "",
    "api_login_path": "",
    "login_path": "/#/Login",
    "username": "刘晓潇",
    "password": "",
    "username_field": "userName",
    "password_field": "password",
    "token_storage": "localStorage",
    "token_key": "access_token",
    "use_page_login": False,
    "case_path": "testcases/api",
}


def get_token_from_page(page: Any, storage: str, storage_key: str) -> str:
    """Read the configured token from browser storage after login."""
    if storage not in {"localStorage", "sessionStorage"}:
        return ""
    token = page.evaluate(
        """([storageName, key]) => {
            try {
                return window[storageName].getItem(key) || "";
            } catch (error) {
                return "";
            }
        }""",
        [storage, storage_key],
    )
    return str(token or "")


def mask_token(token: str) -> str:
    """Mask token for display in the platform response."""
    if not token:
        return ""
    if len(token) <= 12:
        return "*" * len(token)
    return f"{token[:6]}...{token[-6:]}"


def mask_login_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return login result without exposing the full token in the UI."""
    masked = result.copy()
    token = str(masked.pop("token", "") or "")
    masked["token_found"] = bool(token)
    masked["token_preview"] = mask_token(token)
    return masked


def load_config() -> dict[str, Any]:
    """Load saved platform config, falling back to defaults."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        saved_config = json.load(file)
    config = {**DEFAULT_CONFIG, **saved_config}
    if config.get("case_path") == LEGACY_DEFAULT_CASE_PATH:
        config["case_path"] = DEFAULT_CONFIG["case_path"]
    return config


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    """Persist platform config outside source-controlled files."""
    merged_config = {**DEFAULT_CONFIG, **config}
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(merged_config, file, ensure_ascii=False, indent=2)
    return merged_config


def build_url(base_url: str, path: str) -> str:
    """Join host and hash route without losing the hash segment."""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def test_login(config: dict[str, Any]) -> dict[str, Any]:
    """Open the configured login page and submit the configured account."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "ok": False,
            "message": "当前 Python 环境未安装 playwright，请先安装 requirements.txt",
        }

    login_url = build_url(config["base_url"], config["login_path"])
    username = str(config.get("username", ""))
    password = str(config.get("password", ""))
    username_field = str(config.get("username_field", "userName"))
    password_field = str(config.get("password_field", "password"))
    token_storage = str(config.get("token_storage", "localStorage"))
    token_key = str(config.get("token_key", "access_token"))
    timeout = 10000

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            page.goto(login_url, wait_until="domcontentloaded", timeout=timeout)
            page.locator(f"input[name='{username_field}']").first.fill(
                username, timeout=timeout
            )
            password_input = page.locator(f"input[name='{password_field}']").first
            try:
                password_input.fill(password, timeout=timeout)
            except PlaywrightTimeoutError:
                pass

            login_button = page.locator(
                "button:has-text('登录'), [role='button']:has-text('登录'), text=登录"
            ).first
            login_button.click(timeout=timeout)
            page.wait_for_load_state("domcontentloaded", timeout=timeout)
            try:
                page.wait_for_url(lambda url: "Login" not in url, timeout=timeout)
            except PlaywrightTimeoutError:
                pass

            storage_state = context.storage_state()
            current_url = page.url
            token = get_token_from_page(page, token_storage, token_key)
            ok = bool(token) or "Login" not in current_url
            return {
                "ok": ok,
                "message": "登录成功" if ok else "已提交登录，但未获取到 token",
                "url": current_url,
                "token": token,
                "token_storage": token_storage,
                "token_key": token_key,
                "storage_state": storage_state,
            }
        finally:
            context.close()
            browser.close()


def run_pytest(config: dict[str, Any]) -> dict[str, Any]:
    """Run the selected pytest case with platform-provided API config."""
    case_path = str(config.get("case_path", DEFAULT_CONFIG["case_path"]))
    target = ROOT_DIR / case_path
    if not target.exists():
        return {
            "ok": False,
            "return_code": 2,
            "output": f"用例文件不存在: {target}",
        }

    env = os.environ.copy()
    env["BASE_URL"] = str(config.get("base_url", DEFAULT_CONFIG["base_url"]))
    api_base_url = str(config.get("api_base_url") or "")
    api_login_path = str(config.get("api_login_path") or "")
    if api_base_url:
        env["API_BASE_URL"] = api_base_url
    if api_login_path:
        env["API_LOGIN_PATH"] = api_login_path
    env["LOGIN_USERNAME"] = str(config.get("username", ""))
    env["LOGIN_PASSWORD"] = str(config.get("password", ""))
    env["AUTH_STORAGE"] = str(
        config.get("token_storage", DEFAULT_CONFIG["token_storage"])
    )
    env["AUTH_STORAGE_KEY"] = str(config.get("token_key", DEFAULT_CONFIG["token_key"]))

    use_page_login = config.get("use_page_login") in {True, "true", "on", "1", "yes"}
    if use_page_login and not env.get("ACCESS_TOKEN"):
        login_result = test_login(config)
        if not login_result.get("ok"):
            return {
                "ok": False,
                "return_code": 2,
                "output": json.dumps(login_result, ensure_ascii=False, indent=2),
            }
        token = str(login_result.get("token") or "")
        if token:
            env["ACCESS_TOKEN"] = token

    command = [sys.executable, "-m", "pytest", case_path]
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT_DIR),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "ok": False,
            "return_code": 124,
            "output": error.stdout or "执行超时",
        }

    return {
        "ok": completed.returncode == 0,
        "return_code": completed.returncode,
        "output": completed.stdout,
    }


class PlatformHandler(BaseHTTPRequestHandler):
    """HTTP endpoints for the local test platform."""

    def do_HEAD(self) -> None:
        route = urlparse(self.path).path
        if route == "/":
            self.send_file_headers(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/":
            self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if route == "/api/config":
            self.send_json({"ok": True, "config": load_config()})
            return
        if route.startswith("/static/"):
            static_path = STATIC_DIR / route.removeprefix("/static/")
            content_type = "text/plain; charset=utf-8"
            if static_path.suffix == ".css":
                content_type = "text/css; charset=utf-8"
            elif static_path.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            self.send_file(static_path, content_type)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        payload = self.read_json()
        if route == "/api/config":
            self.send_json({"ok": True, "config": save_config(payload)})
            return
        if route == "/api/login/check":
            config = save_config(payload)
            self.send_json(mask_login_result(test_login(config)))
            return
        if route == "/api/run":
            config = save_config(payload)
            self.send_json(run_pytest(config))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file() or STATIC_DIR not in path.resolve().parents:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file_headers(self, path: Path, content_type: str) -> None:
        if not path.is_file() or STATIC_DIR not in path.resolve().parents:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        sys.stdout.write("%s - %s\n" % (self.address_string(), format % args))


def main() -> None:
    host = "127.0.0.1"
    port = int(os.getenv("PLATFORM_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), PlatformHandler)
    print(f"测试平台已启动: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
