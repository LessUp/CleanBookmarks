# 2025-12-14 pyproject.toml 依赖版本下限对齐

- 修改 `pyproject.toml`：
  - `project.dependencies` 补齐 `>=` 版本下限，使其与 `requirements.txt` 保持一致。

影响：
- `pip install .` / `pipx install .` 的依赖解析与 `requirements.txt` 一致，升级策略更明确。
