# 2025-12-18 EnhancedClassifier ML 可用性判定修复

- 修改 `src/enhanced_classifier.py`：
  - 修复 ML 依赖可用性判断：
    - 由“能否导入 `MLClassifierWrapper`”改为读取 `src.ml_classifier.ML_AVAILABLE` 的真实状态。
    - 避免在缺少 `scikit-learn` 时初始化 `EnhancedClassifier` 直接抛 `ImportError` 导致崩溃。
  - 增强初始化的健壮性：
    - 初始化 `MLClassifierWrapper()` 失败时捕获异常并降级为不启用 ML。
  - 修复配置加载阶段日志引用问题：
    - `_load_config()` 在 `self.logger` 尚未初始化时，改用 `logging.getLogger(__name__)` 输出错误日志。

影响：
- 缺少 `scikit-learn` 等机器学习依赖时，`EnhancedClassifier` 可以正常导入与实例化（自动降级为不启用 ML）。
