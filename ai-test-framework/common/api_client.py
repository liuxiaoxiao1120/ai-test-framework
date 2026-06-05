"""兼容入口：保留 ApiClient 名称，实际能力由 core.client.HttpClient 提供。"""

from __future__ import annotations

from core.client import HttpClient


class ApiClient(HttpClient):
    """向后兼容旧导入路径 common.api_client.ApiClient。"""
