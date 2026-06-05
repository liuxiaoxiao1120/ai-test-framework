"""接口用例上下文变量管理。"""

from __future__ import annotations

import os
import re
from typing import Any


VARIABLE_PATTERN = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class CaseContext:
    """保存跨接口用例共享的变量，并递归替换 ${name}。"""

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self.variables: dict[str, Any] = initial.copy() if initial else {}

    def set(self, name: str, value: Any) -> None:
        """写入上下文变量。"""
        self.variables[name] = value

    def get(self, name: str) -> Any:
        """读取上下文变量；优先本地变量，再读系统环境变量。"""
        if name in self.variables:
            return self.variables[name]
        if name in os.environ:
            return os.environ[name]
        raise KeyError(f"变量未定义: {name}")

    def resolve(self, value: Any) -> Any:
        """递归解析 dict/list/string 中的 ${变量}。"""
        if isinstance(value, dict):
            return {key: self.resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.resolve(item) for item in value]
        if isinstance(value, str):
            return self._resolve_string(value)
        return value

    def _resolve_string(self, value: str) -> str:
        def replace(match: re.Match[str]) -> str:
            return str(self.get(match.group(1)))

        return VARIABLE_PATTERN.sub(replace, value)

