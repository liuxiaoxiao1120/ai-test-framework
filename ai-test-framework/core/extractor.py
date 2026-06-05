"""响应字段提取。"""

from __future__ import annotations

import re
from typing import Any


TOKEN_PATTERN = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_]*)|\[(\d+)\]")
MISSING = object()


def jsonpath_get(data: Any, path: str, default: Any = MISSING) -> Any:
    """读取简化 JSONPath，支持 $.a.b、$.a[0].b 和 $。"""
    normalized = path.strip()
    if normalized == "$":
        return data
    if not normalized.startswith("$"):
        normalized = f"$.{normalized.lstrip('.')}"

    current = data
    position = 1
    while position < len(normalized):
        match = TOKEN_PATTERN.match(normalized, position)
        if not match:
            if default is not MISSING:
                return default
            raise KeyError(f"不支持或不存在的 JSONPath: {path}")

        key, index = match.groups()
        if key is not None:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                if default is not MISSING:
                    return default
                raise KeyError(f"JSONPath 不存在: {path}")
        else:
            item_index = int(index)
            if isinstance(current, list) and item_index < len(current):
                current = current[item_index]
            else:
                if default is not MISSING:
                    return default
                raise KeyError(f"JSONPath 不存在: {path}")
        position = match.end()
    return current


class Extractor:
    """按 YAML extract 配置把响应字段提取为上下文变量。"""

    def extract(self, response: Any, extract_config: dict[str, str] | None) -> dict[str, Any]:
        """执行字段提取。"""
        if not extract_config:
            return {}

        json_body = self._json(response)
        values: dict[str, Any] = {}
        for name, expression in extract_config.items():
            expr = str(expression)
            if expr.startswith("$.") or expr == "$":
                values[name] = jsonpath_get(json_body, expr)
            elif expr.startswith("header."):
                values[name] = response.headers.get(expr.removeprefix("header."))
            elif expr == "status_code":
                values[name] = response.status_code
            else:
                raise ValueError(f"不支持的提取表达式: {expr}")
        return values

    def _json(self, response: Any) -> Any:
        try:
            return response.json()
        except ValueError:
            return {}

