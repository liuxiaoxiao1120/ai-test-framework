"""使用 Playwright 抓取页面接口，并生成 YAML 用例草稿。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml


def normalize_case_id(method: str, path: str, index: int) -> str:
    """根据请求方法和路径生成稳定的用例 id。"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", path.strip("/")).strip("_").lower()
    return f"{method.lower()}_{slug or 'root'}_{index}"


def parse_params(query: str) -> dict[str, Any]:
    """把 URL query 转成 YAML 友好的参数字典。"""
    parsed = parse_qs(query, keep_blank_values=True)
    result: dict[str, Any] = {}
    for key, values in parsed.items():
        result[key] = values[0] if len(values) == 1 else values
    return result


def build_case(response: Any, index: int) -> dict[str, Any]:
    """把 Playwright response 转换为一条 YAML 用例草稿。"""
    request = response.request
    parsed_url = urlparse(response.url)
    method = request.method.upper()
    content_type = response.headers.get("content-type", "")

    request_block: dict[str, Any] = {"method": method, "url": parsed_url.path or "/"}
    params = parse_params(parsed_url.query)
    if params:
        request_block["params"] = params

    try:
        post_data = request.post_data_json()
    except Exception:
        post_data = None
    if post_data:
        request_block["json"] = post_data

    assert_block: dict[str, Any] = {"status_code": response.status}
    if "json" in content_type.lower():
        assert_block["jsonpath"] = {}

    return {
        "id": normalize_case_id(method, parsed_url.path, index),
        "name": f"{method} {parsed_url.path or '/'}",
        "enabled": False,
        "request": request_block,
        "assert": assert_block,
    }


def capture(args: argparse.Namespace) -> None:
    """启动浏览器并监听页面接口。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError("未安装 playwright，请先安装可选抓取依赖") from error

    cases: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    keywords = [keyword.lower() for keyword in args.keyword]

    def on_response(response: Any) -> None:
        request = response.request
        if request.resource_type not in {"xhr", "fetch"}:
            return
        url = response.url.lower()
        if keywords and not any(keyword in url for keyword in keywords):
            return
        key = (request.method, response.url)
        if key in seen:
            return
        seen.add(key)
        cases.append(build_case(response, len(cases) + 1))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        context = browser.new_context(storage_state=args.storage_state or None)
        page = context.new_page()
        page.on("response", on_response)
        page.goto(args.url, wait_until="domcontentloaded", timeout=args.timeout)
        page.wait_for_timeout(args.wait_seconds * 1000)
        context.close()
        browser.close()

    suite = {
        "suite": args.suite,
        "description": "由 Playwright 页面接口抓取生成，请审阅路径、参数、鉴权和断言后启用。",
        "defaults": {
            "auth": True,
            "request": {"headers": {"Accept": "application/json"}},
        },
        "cases": cases,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(suite, file, allow_unicode=True, sort_keys=False)
    print(f"已生成 YAML 草稿: {output_path}，接口数量: {len(cases)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取页面接口并生成 YAML 用例草稿")
    parser.add_argument("url", help="需要打开并监听接口的页面地址")
    parser.add_argument(
        "-o",
        "--output",
        default="cases/captured/api_cases.yaml",
        help="输出 YAML 文件路径",
    )
    parser.add_argument("--suite", default="页面抓取接口", help="YAML suite 名称")
    parser.add_argument(
        "-k",
        "--keyword",
        action="append",
        default=[],
        help="只保留 URL 中包含该关键字的接口，可重复传入",
    )
    parser.add_argument(
        "--storage-state",
        default="",
        help="Playwright storage_state JSON 文件，用于复用已登录状态",
    )
    parser.add_argument("--wait-seconds", type=int, default=20, help="页面监听秒数")
    parser.add_argument("--timeout", type=int, default=10000, help="页面打开超时时间")
    parser.add_argument("--headless", action="store_true", help="使用无头浏览器")
    capture(parser.parse_args())


if __name__ == "__main__":
    main()
