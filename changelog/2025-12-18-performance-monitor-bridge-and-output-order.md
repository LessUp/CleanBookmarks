# 2025-12-18 性能监控桥接与导出顺序稳定化

- 修改 `src/placeholder_modules.py`：
  - 将占位 `PerformanceMonitor` 升级为“优先桥接”模式：
    - 若可导入 `src.performance_optimizer.PerformanceMonitor`，则内部委托到完整实现。
    - 若依赖缺失（例如 `psutil`）或初始化失败，则自动降级为最小占位实现，不影响主流程导入/运行。
  - 提供 `get_summary()` 兼容接口（代理到 `get_performance_summary()`），并通过 `__getattr__` 代理其它可用方法。

- 修改 `src/bookmark_processor.py`：
  - 强化 `_sort_organized_structure()` 的稳定排序：
    - 顶层 subject（导出主分类）优先按 `config.json` 的 `category_order`（并经 `TaxonomyStandardizer.normalize_subject` 标准化）排序。
    - 未出现在 `category_order` 的分类按书签数量降序、名称升序排序。
    - 子分类（resource_type）按数量降序、名称升序稳定排序；每个列表内部按 `confidence` 降序排序。

影响：
- 性能监控在依赖齐全时可获得更完整的统计能力，缺依赖时保持优雅降级。
- 导出/报告结构的主分类与子分类顺序更加可预测，便于对比与复盘。
