"""接口 YAML 执行器的本地单元测试。"""

from __future__ import annotations

from common.api_case_runner import ApiCaseRunner


class FakeElapsed:
    def total_seconds(self) -> float:
        return 0.01


class FakeRequest:
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
    def request(self, method: str, path: str, **kwargs):
        assert method == "GET"
        assert path == "/api/health"
        assert kwargs["params"] == {"id": "R001"}
        return FakeResponse()


def test_api_case_runner_supports_variables_extract_and_assertions() -> None:
    runner = ApiCaseRunner(FakeClient(), variables={"route_id": "R001"})
    case = {
        "name": "健康检查",
        "request": {
            "method": "GET",
            "path": "/api/health",
            "params": {"id": "{{ route_id }}"},
        },
        "extract": {"response_id": "json:data.id"},
        "assertions": [
            {"type": "status_code", "expected": 200, "message": "状态码应为 200"},
            {"type": "json_path_equal", "path": "code", "expected": 0},
            {"type": "json_path_exists", "path": "data.id"},
        ],
    }

    runner.run_case(case)

    assert runner.variables["response_id"] == "R001"
