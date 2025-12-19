# 2025-12-19 置信度阈值强制未分类 + 规则引擎扩展字段

- 修改 `src/ai_classifier.py`：
  - `AIBookmarkClassifier` 支持注入已加载的 `config`（便于运行时覆盖配置而不改写 `config.json`）。
  - 在 `_ensemble_classification()` 融合阶段强制应用 `ai_settings.confidence_threshold`：
    - 若最终 `confidence < threshold`，则将 `category` 置为 `"未分类"`。
    - 保留原推理 `reasoning`，并追加“低于阈值”说明。
    - 将原本的最佳分类与其置信度放入 `alternatives` 供参考。

- 修改 `src/bookmark_processor.py`：
  - `BookmarkProcessor` 新增 `confidence_threshold` 参数，用于运行时覆盖 `ai_settings.confidence_threshold`。
  - 初始化时记录配置加载是否成功（避免加载失败时向分类器注入空配置）。
  - 创建 `AIBookmarkClassifier` 时注入已归一化后的配置，并同步写入阈值覆盖。

- 修改 `main.py`：
  - 批处理模式下创建 `BookmarkProcessor` 时传入 `--threshold`，使 CLI 运行时阈值覆盖真正生效。

- 修改 `src/rule_engine.py`：
  - 扩展规则字段能力：支持 `match=url_ends_with` 与 `match_all_keywords_in`。
  - 按 `processing_order` 顺序将 `priority_rules` 与 `category_rules` 一并纳入预编译与匹配流程。
