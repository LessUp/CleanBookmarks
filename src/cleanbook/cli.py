"""CleanBook 统一命令入口

提供一个薄封装，直接复用项目根的 main.main()
"""
from __future__ import annotations


def main():
    # 复用现有 CLI 逻辑，避免重复实现
    from main import main as _entry
    _entry()
