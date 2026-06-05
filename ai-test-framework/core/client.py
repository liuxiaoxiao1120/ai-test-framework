"""HTTP 请求封装。"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

import requests


class HttpClient:
    """基于 requests.Session 的接口测试客户端。"""

    def __init__(
        self,
        base_url: str,
        timeout: int = 10000,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/" if base_url else ""
        self.timeout = timeout / 1000
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)

    def build_url(self, url: str) -> str:
        """拼接 base_url 和接口相对路径；完整 URL 原样返回。"""
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return url
        return urljoin(self.base_url, url.lstrip("/"))

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        **kwargs: Any,
    ) -> requests.Response:
        """发送 HTTP 请求，支持 GET/POST/PUT/DELETE 等方法。"""
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(
            method=method.upper(),
            url=self.build_url(url),
            headers=headers,
            params=params,
            json=json,
            data=data,
            **kwargs,
        )

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """发送 GET 请求。"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """发送 POST 请求。"""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        """发送 PUT 请求。"""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        """发送 DELETE 请求。"""
        return self.request("DELETE", url, **kwargs)

