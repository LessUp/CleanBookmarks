# 2025-12-14 测试套件健壮性增强（可选依赖/自动跳过）

- 修改 `tests/test_suite.py`：
  - 将被测模块按组件分开导入，并在导入失败时自动降级为 `unittest.skip`，避免缺少可选依赖时出现 `NameError`；
  - 增加 `psutil` 可选检测，未安装时自动跳过内存相关测试；
  - 保持 `python tests/test_suite.py` 在最小环境可运行（核心测试通过，其余按依赖自动跳过）。
