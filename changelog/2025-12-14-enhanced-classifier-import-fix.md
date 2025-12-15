# 2025-12-14 打包兼容性修复（EnhancedClassifier 导入路径）

- 修改 `src/enhanced_classifier.py`：
  - 机器学习包装器 `MLClassifierWrapper` 优先使用相对导入 `from .ml_classifier import MLClassifierWrapper`；
  - 保留脚本直跑场景下的回退导入（`from ml_classifier import ...`）。

影响：
- `pipx install .` / `pip install .` 后通过 console script 调用时，模块导入更稳定。
