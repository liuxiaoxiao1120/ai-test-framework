"""YAML 驱动的接口自动化用例入口。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import allure
import pytest

from common.api_case_runner import ApiCaseRunner
from common.yaml_util import YamlUtil


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASE_DIR = PROJECT_ROOT / "data" / "api"


def _case_files() -> list[Path]:
    configured = os.getenv("API_CASE_PATH")
    if configured:
        path = PROJECT_ROOT / configured
        if path.is_file():
            return [path]
        return sorted(path.rglob("*.yaml"))
    return sorted(DEFAULT_CASE_DIR.rglob("*.yaml"))


def _load_yaml_cases() -> list[Any]:
    params: list[Any] = []
    for file_path in _case_files():
        suite = YamlUtil.load_yaml(file_path)
        defaults = suite.get("defaults", {})
        for index, case in enumerate(suite.get("cases", []), start=1):
            if not case.get("enabled", True):
                continue
            case_id = str(case.get("id") or case.get("name") or f"case_{index}")
            params.append(pytest.param(file_path, suite, defaults, case, id=case_id))
    return params


@pytest.mark.parametrize(
    "source_path,suite,defaults,case",
    _load_yaml_cases(),
)
def test_api_yaml_case(
    source_path: Path,
    suite: dict[str, Any],
    defaults: dict[str, Any],
    case: dict[str, Any],
    api_client,
    request: pytest.FixtureRequest,
) -> None:
    """读取 YAML 用例并通过 Requests 执行接口测试。"""
    if case.get("auth", defaults.get("auth", False)):
        auth_api_client = request.getfixturevalue("auth_api_client")
    else:
        auth_api_client = None

    allure.dynamic.epic("接口自动化")
    allure.dynamic.feature(str(suite.get("suite") or source_path.stem))
    allure.dynamic.title(str(case.get("name") or case.get("id")))

    runner = ApiCaseRunner(api_client=api_client, auth_api_client=auth_api_client)
    runner.run_case(case=case, defaults=defaults, source_path=source_path)
