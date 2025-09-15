# 2025-09-15 目录与发布重构（CLI/打包/分类调整）

## 概述
- 移除 `config.json` 中“💼 求职”分类（分类顺序与规则）。
- 新增标准打包文件 `pyproject.toml`，提供命令入口：`cleanbook`、`cleanbook-wizard`。
- 新增包结构入口：`src/cleanbook/cli.py`（复用 `main.py`）。
- 新增中文快速上手：`docs/quickstart_zh.md`。
- 调整导入与包声明：新增 `src/__init__.py`、`src/cleanbook/__init__.py`。

## 建议的后续清理（待确认）
- 归档或删除历史/重复文件：
  - 顶层 `cleanbook/` 旧目录（与 `src/cleanbook/` 重复）。
  - `doc/` 旧文档目录（已迁移至 `docs/`）。
- 若需要发布 PyPI：完善 `project.urls`、作者与版本；执行 `python -m build && twine upload dist/*`。

## 影响
- 使用者可通过 pipx 安装并直接运行命令，无需手动进入项目目录。
- 分类顺序不再包含“💼 求职”。
