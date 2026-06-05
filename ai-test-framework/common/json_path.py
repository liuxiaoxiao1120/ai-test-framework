"""兼容入口：JSONPath 读取能力迁移到 core.extractor。"""

from __future__ import annotations

from typing import Any

from core.extractor import MISSING, jsonpath_get


def read_path(data: Any, path: str, default: Any = MISSING) -> Any:
    """兼容旧 read_path 调用。"""
    return jsonpath_get(data, path, default=default)
