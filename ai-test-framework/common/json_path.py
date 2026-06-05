"""轻量 JSON 路径读取工具，支持 data.items.0.id 这类路径。"""

from __future__ import annotations

from typing import Any


MISSING = object()


def read_path(data: Any, path: str, default: Any = MISSING) -> Any:
    """从 dict/list 中读取点分路径；未找到时返回 default 或抛出 KeyError。"""
    normalized = path.strip()
    if normalized.startswith("$."):
        normalized = normalized[2:]
    elif normalized.startswith("$"):
        normalized = normalized[1:].lstrip(".")

    if not normalized:
        return data

    current = data
    for part in normalized.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index < len(current):
                current = current[index]
                continue
        if default is not MISSING:
            return default
        raise KeyError(f"JSON 路径不存在: {path}")
    return current
