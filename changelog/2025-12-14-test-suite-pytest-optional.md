# 2025-12-14 测试套件兼容性修复（pytest 可选）

- 修改 `tests/test_suite.py`：
  - 移除对 `pytest` 的顶层强制导入；
  - 在未安装 pytest 时，`python tests/test_suite.py` 可正常回退到 unittest 运行测试。

兼容性：
- 已安装 pytest 的环境不受影响；
- 未安装 pytest 的环境可继续执行基础回归（unittest 路径）。
