"""项目断言工具：统一输出 Allure 步骤。"""

from typing import Any

import allure


class Assert:
    """封装常用断言，让失败信息保持清晰一致。"""

    @staticmethod
    def is_true(condition: bool, message: str) -> None:
        """断言条件为真。"""
        with allure.step(f"断言：{message}"):
            assert condition, message

    @staticmethod
    def equal(actual: Any, expected: Any, message: str) -> None:
        """断言实际值与预期值一致。"""
        with allure.step(f"断言：{message}"):
            assert actual == expected, (
                f"{message}，实际值: {actual!r}，预期值: {expected!r}"
            )

    @staticmethod
    def not_empty(value: Any, message: str) -> None:
        """断言对象不为空。"""
        with allure.step(f"断言：{message}"):
            assert value, message
