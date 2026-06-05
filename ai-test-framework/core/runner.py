"""接口用例执行器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import allure

from core.assertor import Assertor
from core.client import HttpClient
from core.context import CaseContext
from core.extractor import Extractor
from core.reporter import Reporter


class CaseRunner:
    """执行一条 YAML/JSON 接口用例。"""

    def __init__(
        self,
        client: HttpClient,
        context: CaseContext | None = None,
        assertor: Assertor | None = None,
        extractor: Extractor | None = None,
        reporter: Reporter | None = None,
    ) -> None:
        self.client = client
        self.context = context or CaseContext()
        self.assertor = assertor or Assertor()
        self.extractor = extractor or Extractor()
        self.reporter = reporter or Reporter()

    def run(self, case: dict[str, Any]) -> Any:
        """执行请求、报告、提取变量和断言。"""
        request_config = self.context.resolve(case.get("request", {}))
        if not request_config:
            raise ValueError(f"用例缺少 request: {case.get('name')}")

        method = str(request_config.get("method", "GET")).upper()
        url = request_config.get("url") or request_config.get("path")
        if not url:
            raise ValueError(f"用例缺少 request.url: {case.get('name')}")

        with allure.step(f"发送接口请求：{case.get('name')}"):
            response = self.client.request(
                method=method,
                url=str(url),
                headers=request_config.get("headers"),
                params=request_config.get("params"),
                json=request_config.get("json"),
                data=request_config.get("data"),
            )

        source = case.get("_source")
        self.reporter.attach_exchange(
            case,
            response,
            source_path=source if isinstance(source, Path) else None,
        )

        extracted = self.extractor.extract(response, case.get("extract"))
        for name, value in extracted.items():
            self.context.set(name, value)

        self.assertor.assert_response(response, case.get("assert"))
        return response

