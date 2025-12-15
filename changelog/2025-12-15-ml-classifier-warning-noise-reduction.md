# 2025-12-15 降低 ML 模型加载/训练的警告噪音

- 修改 `src/ml_classifier.py`：
  - `LogisticRegression` 移除 `n_jobs` 参数，避免 sklearn 1.8+ 的 `FutureWarning`（该参数已不生效）。
  - 在 `load_model()` 中捕获并汇总 `InconsistentVersionWarning`，避免同一类警告在多次加载时重复刷屏；同时输出一次性的提示信息，建议在 sklearn 升级后重新训练模型。
  - 在训练完成写入 `training_stats` 时记录运行环境版本信息（Python / NumPy / sklearn），便于后续排查模型兼容性。

影响：
- `pytest` 输出更干净，减少因模型历史文件导致的大量重复 warning；同时保留对“版本不一致模型加载风险”的可见提示。
