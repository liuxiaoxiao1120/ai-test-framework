"""接口测试入口示例。"""

import os

import pytest


def test_api_base_url_configured(api_base_url: str) -> None:
    """确认接口基础地址可从配置读取。"""
    assert api_base_url.startswith(("http://", "https://"))


def test_api_smoke_path(api_client) -> None:
    """设置 API_SMOKE_PATH 后，可用这个用例验证一个无需登录的接口。"""
    path = os.getenv("API_SMOKE_PATH")
    if not path:
        pytest.skip("未设置 API_SMOKE_PATH，跳过接口连通性示例")

    response = api_client.get(path)
    assert response.status_code == 200


def test_auth_api_smoke_path(request: pytest.FixtureRequest) -> None:
    """设置 AUTH_API_SMOKE_PATH 后，可用这个用例验证一个需要登录的接口。"""
    path = os.getenv("AUTH_API_SMOKE_PATH")
    if not path:
        pytest.skip("未设置 AUTH_API_SMOKE_PATH，跳过鉴权接口示例")

    auth_api_client = request.getfixturevalue("auth_api_client")
    response = auth_api_client.get(path)
    assert response.status_code == 200
