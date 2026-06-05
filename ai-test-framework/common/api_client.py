"""接口测试 HTTP 客户端封装。"""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urljoin


class ApiClient:
    """基于 requests.Session 的轻量接口请求客户端。"""

    def __init__(
        self,
        base_url: str,
        timeout: int = 10000,
        default_headers: Optional[dict[str, str]] = None,
    ) -> None:
        try:
            import requests
        except ImportError as error:
            raise RuntimeError("缺少 requests 依赖，请先安装 requirements.txt") from error

        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout / 1000
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)

    def build_url(self, path: str) -> str:
        """拼接接口基础地址和接口路径。"""
        return urljoin(self.base_url, path.lstrip("/"))

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """发送 HTTP 请求并返回原始 response，便于用例自定义断言。"""
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, self.build_url(path), **kwargs)

    def get(self, path: str, **kwargs: Any) -> Any:
        """发送 GET 请求。"""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        """发送 POST 请求。"""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        """发送 PUT 请求。"""
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        """发送 DELETE 请求。"""
        return self.request("DELETE", path, **kwargs)
