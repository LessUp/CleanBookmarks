# 2025-12-14 增加 CI 与开发依赖清单

- 新增 GitHub Actions CI：`.github/workflows/ci.yml`
  - Python 版本矩阵：3.10 / 3.11 / 3.12
  - 安装方式：`pip install .`
  - 测试：`pytest -q`

- 新增 `requirements-dev.txt`
  - 提供 `black` / `flake8` / `mypy` 及常用类型 stub（`types-requests`、`types-PyYAML`）

影响：
- PR/提交可自动验证“可安装 + 可测试”，为后续引入 lint/typecheck 的强制门禁打基础。
