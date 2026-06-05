"""YAML/JSON 接口用例加载。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class CaseLoader:
    """从 cases 目录加载 YAML/JSON 接口用例。"""

    def __init__(self, case_root: Path) -> None:
        self.case_root = case_root

    def discover(self, target: str | Path | None = None) -> list[Path]:
        """发现用例文件；target 可以是文件或目录。"""
        root = Path(target) if target else self.case_root
        if not root.is_absolute():
            root = self.case_root.parents[0] / root
        if root.is_file():
            return [root]
        patterns = ("*.yaml", "*.yml", "*.json")
        files: list[Path] = []
        for pattern in patterns:
            files.extend(root.rglob(pattern))
        return sorted(files)

    def load_file(self, file_path: Path) -> list[dict[str, Any]]:
        """加载一个文件，兼容单用例、用例列表和 suite.cases。"""
        data = self._read(file_path)
        raw_cases: list[dict[str, Any]]
        if isinstance(data, list):
            raw_cases = data
            suite_name = file_path.stem
        elif isinstance(data, dict) and "cases" in data:
            raw_cases = data.get("cases") or []
            suite_name = str(data.get("name") or data.get("suite") or file_path.stem)
        elif isinstance(data, dict):
            raw_cases = [data]
            suite_name = str(data.get("suite") or file_path.parent.name)
        else:
            raise ValueError(f"用例文件格式不支持: {file_path}")

        cases = []
        for index, case in enumerate(raw_cases, start=1):
            if not isinstance(case, dict):
                raise ValueError(f"用例必须是字典: {file_path}")
            normalized = case.copy()
            normalized.setdefault("name", f"{file_path.stem}_{index}")
            normalized["_suite"] = suite_name
            normalized["_source"] = file_path
            cases.append(normalized)
        return cases

    def load_cases(self, target: str | Path | None = None) -> list[dict[str, Any]]:
        """加载所有启用的接口用例。"""
        cases: list[dict[str, Any]] = []
        for file_path in self.discover(target):
            for case in self.load_file(file_path):
                if case.get("enabled", True):
                    cases.append(case)
        return cases

    def _read(self, file_path: Path) -> Any:
        with file_path.open("r", encoding="utf-8") as file:
            if file_path.suffix == ".json":
                return json.load(file)
            return yaml.safe_load(file) or {}

