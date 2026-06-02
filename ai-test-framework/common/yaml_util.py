"""YAML 配置读取工具。"""

from pathlib import Path
from typing import Any, Union

import yaml


class YamlUtil:
    """提供统一的 YAML 文件读取入口。"""

    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> dict[str, Any]:
        """读取 YAML 文件，并确保顶层结构为字典。"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML 文件不存在: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        if not isinstance(data, dict):
            raise ValueError(f"YAML 顶层结构必须为字典: {path}")
        return data
