"""YAML/JSON 驱动的接口自动化用例入口。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import allure
import pytest

from core.context import CaseContext
from core.loader import CaseLoader
from core.runner import CaseRunner


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASE_DIR = PROJECT_ROOT / "cases"


def _load_cases() -> list[Any]:
    loader = CaseLoader(DEFAULT_CASE_DIR)
    target = os.getenv("API_CASE_PATH")
    cases = loader.load_cases(target)
    if not cases:
        return [
            pytest.param(
                {
                    "name": "未发现已启用接口用例",
                    "_suite": "接口自动化",
                    "_source": DEFAULT_CASE_DIR,
                },
                marks=pytest.mark.skip(reason="未发现已启用接口用例"),
                id="no_enabled_cases",
            )
        ]
    return [
        pytest.param(case, id=str(case.get("id") or case.get("name")))
        for case in cases
    ]


@pytest.fixture(scope="session")
def api_context() -> CaseContext:
    """跨接口用例共享提取出的变量。"""
    return CaseContext()


@pytest.mark.parametrize("case", _load_cases())
def test_api_yaml_case(
    case: dict[str, Any],
    api_client,
    api_context: CaseContext,
) -> None:
    """读取 YAML/JSON 用例并通过 Requests 执行接口测试。"""
    allure.dynamic.epic("接口自动化")
    allure.dynamic.feature(str(case.get("_suite") or "接口用例"))
    allure.dynamic.title(str(case.get("name")))

    runner = CaseRunner(client=api_client, context=api_context)
    runner.run(case)
