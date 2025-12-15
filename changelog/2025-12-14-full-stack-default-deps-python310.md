# 2025-12-14 全家桶默认依赖 + Python 版本下限提升

- 修改 `pyproject.toml`：
  - `requires-python` 提升为 `>=3.10`；
  - `project.dependencies` 按“全家桶默认安装”策略与 `requirements.txt` 对齐，补齐：
    - `matplotlib`、`seaborn`
    - `watchdog`
    - `pytest`、`pytest-cov`

影响：
- `pip install .` / `pipx install .` 默认安装包含开发/测试/可视化等依赖的全量能力；
- Python 3.9 及以下环境将不再满足安装约束。
