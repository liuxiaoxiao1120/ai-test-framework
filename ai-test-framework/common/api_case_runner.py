"""YAML 接口用例执行器。"""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

import allure

from common.api_client import ApiClient
from common.assertion import Assert
from common.json_path import MISSING, read_path


VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
ENV_PATTERN = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class ApiCaseRunner:
    """执行 YAML 中定义的接口测试用例。"""

    def __init__(
        self,
        api_client: ApiClient,
        auth_api_client: Optional[ApiClient] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> None:
        self.api_client = api_client
        self.auth_api_client = auth_api_client
        self.variables = variables or {}

    def run_case(
        self,
        case: dict[str, Any],
        defaults: Optional[dict[str, Any]] = None,
        source_path: Optional[Path] = None,
    ) -> None:
        """执行单条 YAML 用例，并完成请求、提取和断言。"""
        defaults = defaults or {}
        request_config = self._build_request(case, defaults)
        client = self._select_client(case, defaults)

        title = str(case.get("name") or case.get("id") or request_config["path"])
        with allure.step(f"请求接口：{title}"):
            response = client.request(
                request_config["method"],
                request_config["path"],
                params=request_config.get("params"),
                json=request_config.get("json"),
                data=request_config.get("data"),
                headers=request_config.get("headers"),
            )

        self._attach_request_response(case, request_config, response, source_path)
        self._extract(case.get("extract", {}), response)
        self._assert_response(case.get("assertions", []), response)

    def _select_client(
        self, case: dict[str, Any], defaults: dict[str, Any]
    ) -> ApiClient:
        auth_required = bool(case.get("auth", defaults.get("auth", False)))
        if not auth_required:
            return self.api_client
        if self.auth_api_client is None:
            raise AssertionError("该用例需要鉴权客户端，但当前未提供 auth_api_client")
        return self.auth_api_client

    def _build_request(
        self, case: dict[str, Any], defaults: dict[str, Any]
    ) -> dict[str, Any]:
        default_request = deepcopy(defaults.get("request", {}))
        case_request = deepcopy(case.get("request", {}))
        request_config = {**default_request, **case_request}

        headers = {
            **deepcopy(default_request.get("headers", {})),
            **deepcopy(case_request.get("headers", {})),
        }
        if headers:
            request_config["headers"] = headers

        request_config.setdefault("method", "GET")
        if "path" not in request_config:
            raise ValueError(f"接口用例缺少 request.path: {case}")
        request_config["method"] = str(request_config["method"]).upper()
        return self._render(request_config)

    def _render(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._render(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._render(item) for item in value]
        if isinstance(value, str):
            return self._render_string(value)
        return value

    def _render_string(self, value: str) -> str:
        def replace_variable(match: re.Match[str]) -> str:
            name = match.group(1)
            if name in self.variables:
                return str(self.variables[name])
            if name in os.environ:
                return os.environ[name]
            raise KeyError(f"变量未定义: {name}")

        def replace_env(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in os.environ:
                raise KeyError(f"环境变量未定义: {name}")
            return os.environ[name]

        rendered = VARIABLE_PATTERN.sub(replace_variable, value)
        return ENV_PATTERN.sub(replace_env, rendered)

    def _extract(self, extract_config: Any, response: Any) -> None:
        if not extract_config:
            return
        if not isinstance(extract_config, dict):
            raise ValueError("extract 必须是字典，例如 token: json:data.token")

        json_body = self._safe_json(response)
        for name, expression in extract_config.items():
            value = self._read_expression(response, json_body, str(expression))
            self.variables[str(name)] = value

    def _assert_response(self, assertions: Any, response: Any) -> None:
        if not assertions:
            return
        if not isinstance(assertions, list):
            raise ValueError("assertions 必须是列表")

        json_body = self._safe_json(response)
        for assertion in assertions:
            if not isinstance(assertion, dict):
                raise ValueError(f"断言必须是字典: {assertion}")
            assertion_type = str(assertion.get("type", "")).strip()
            message = str(assertion.get("message") or assertion_type)
            expected = assertion.get("expected")

            if assertion_type == "status_code":
                Assert.equal(response.status_code, int(expected), message)
            elif assertion_type == "response_time_less_than":
                elapsed_ms = response.elapsed.total_seconds() * 1000
                Assert.is_true(elapsed_ms < float(expected), message)
            elif assertion_type == "body_contains":
                Assert.is_true(str(expected) in response.text, message)
            elif assertion_type == "body_not_contains":
                Assert.is_true(str(expected) not in response.text, message)
            elif assertion_type == "header_equal":
                actual = response.headers.get(str(assertion["name"]))
                Assert.equal(actual, str(expected), message)
            elif assertion_type == "header_contains":
                actual = response.headers.get(str(assertion["name"]), "")
                Assert.is_true(str(expected) in actual, message)
            elif assertion_type == "json_path_equal":
                actual = read_path(json_body, str(assertion["path"]))
                Assert.equal(actual, expected, message)
            elif assertion_type == "json_path_exists":
                actual = read_path(json_body, str(assertion["path"]), default=MISSING)
                Assert.is_true(actual is not MISSING, message)
            elif assertion_type == "json_path_not_empty":
                actual = read_path(json_body, str(assertion["path"]))
                Assert.not_empty(actual, message)
            elif assertion_type == "json_path_contains":
                actual = read_path(json_body, str(assertion["path"]))
                Assert.is_true(expected in actual, message)
            elif assertion_type == "json_path_length":
                actual = read_path(json_body, str(assertion["path"]))
                Assert.equal(len(actual), int(expected), message)
            else:
                raise ValueError(f"不支持的断言类型: {assertion_type}")

    def _read_expression(self, response: Any, json_body: Any, expression: str) -> Any:
        if expression.startswith("json:"):
            return read_path(json_body, expression.removeprefix("json:"))
        if expression.startswith("header:"):
            return response.headers.get(expression.removeprefix("header:"), "")
        if expression == "status_code":
            return response.status_code
        if expression == "body":
            return response.text
        raise ValueError(f"不支持的提取表达式: {expression}")

    def _safe_json(self, response: Any) -> Any:
        try:
            return response.json()
        except ValueError:
            return {}

    def _attach_request_response(
        self,
        case: dict[str, Any],
        request_config: dict[str, Any],
        response: Any,
        source_path: Optional[Path],
    ) -> None:
        payload = {
            "case": case.get("name") or case.get("id"),
            "source": str(source_path) if source_path else "",
            "request": {
                "method": request_config.get("method"),
                "url": response.request.url,
                "headers": dict(response.request.headers),
                "body": self._decode_body(response.request.body),
            },
            "response": {
                "status_code": response.status_code,
                "elapsed_ms": round(response.elapsed.total_seconds() * 1000, 2),
                "headers": dict(response.headers),
                "body": self._response_body(response),
            },
        }
        allure.attach(
            json.dumps(payload, ensure_ascii=False, indent=2),
            name="接口请求与响应",
            attachment_type=allure.attachment_type.JSON,
        )

    def _decode_body(self, body: Any) -> Any:
        if body is None:
            return None
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body)

    def _response_body(self, response: Any) -> Any:
        json_body = self._safe_json(response)
        if json_body != {}:
            return json_body
        return response.text
