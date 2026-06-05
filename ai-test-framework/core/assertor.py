"""接口响应断言处理。"""

from __future__ import annotations

from typing import Any

import allure

from core.extractor import MISSING, jsonpath_get


class Assertor:
    """处理 YAML assert 块中的状态码和 JSONPath 断言。"""

    def assert_response(self, response: Any, assert_config: dict[str, Any] | None) -> None:
        """执行响应断言。"""
        if not assert_config:
            return

        if "status_code" in assert_config:
            expected_status = int(assert_config["status_code"])
            with allure.step(f"断言状态码为 {expected_status}"):
                assert response.status_code == expected_status, (
                    f"状态码不符合预期，实际: {response.status_code}，预期: {expected_status}"
                )

        jsonpath_asserts = assert_config.get("jsonpath", {})
        if jsonpath_asserts:
            body = self._json(response)
            for path, expected in jsonpath_asserts.items():
                with allure.step(f"断言 JSONPath {path} 等于 {expected!r}"):
                    actual = jsonpath_get(body, str(path), default=MISSING)
                    assert actual is not MISSING, f"JSONPath 不存在: {path}"
                    assert actual == expected, (
                        f"JSONPath {path} 不符合预期，实际: {actual!r}，预期: {expected!r}"
                    )

    def _json(self, response: Any) -> Any:
        try:
            return response.json()
        except ValueError as error:
            raise AssertionError("响应不是合法 JSON，无法执行 JSONPath 断言") from error

