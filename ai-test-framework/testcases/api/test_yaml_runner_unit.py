"""接口 core 执行器的本地单元测试。"""

from __future__ import annotations

from core.context import CaseContext
from core.runner import CaseRunner


class FakeElapsed:
    def total_seconds(self) -> float:
        return 0.01


class FakeRequest:
    method = "GET"
    url = "http://example.test/api/health"
    headers = {"Content-Type": "application/json"}
    body = None


class FakeResponse:
    status_code = 200
    text = '{"code": 0, "data": {"id": "R001"}}'
    headers = {"Content-Type": "application/json"}
    elapsed = FakeElapsed()
    request = FakeRequest()

    def json(self) -> dict:
        return {"code": 0, "data": {"id": "R001"}}


class FakeClient:
    def request(self, method: str, url: str, **kwargs):
        assert method == "GET"
        assert url == "/api/health"
        assert kwargs["params"] == {"id": "R001"}
        return FakeResponse()


def test_core_runner_supports_variables_extract_and_assertions() -> None:
    context = CaseContext({"route_id": "R001"})
    runner = CaseRunner(FakeClient(), context=context)
    case = {
        "name": "健康检查",
        "request": {
            "method": "GET",
            "url": "/api/health",
            "params": {"id": "${route_id}"},
        },
        "extract": {"response_id": "$.data.id"},
        "assert": {"status_code": 200, "jsonpath": {"$.code": 0}},
    }

    runner.run(case)

    assert context.get("response_id") == "R001"
