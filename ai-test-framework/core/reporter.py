"""接口执行结果整理和 Allure 附件。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import allure


class Reporter:
    """把接口请求和响应整理为报告附件。"""

    def attach_exchange(
        self,
        case: dict[str, Any],
        response: Any,
        source_path: Path | None = None,
    ) -> dict[str, Any]:
        """整理请求响应并附加到 Allure。"""
        result = {
            "case": case.get("name"),
            "source": str(source_path) if source_path else "",
            "request": {
                "method": response.request.method,
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
            json.dumps(result, ensure_ascii=False, indent=2),
            name="接口请求与响应",
            attachment_type=allure.attachment_type.JSON,
        )
        return result

    def _decode_body(self, body: Any) -> Any:
        if body is None:
            return None
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body)

    def _response_body(self, response: Any) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

