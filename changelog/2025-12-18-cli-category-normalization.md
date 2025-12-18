# 2025-12-18 分类名去图标 + CLI 入口收敛

- 修改 `src/bookmark_processor.py`：
  - 初始化时对配置中的分类相关字段进行规范化（去除 emoji/装饰前缀），覆盖：
    - `category_order`
    - `domain_grouping_rules`
    - `priority_rules`
    - `category_rules`
  - 在写入分类结果与统计时，对 `category` 做同样的规范化，确保导出与统计使用不带图标的分类名。

- 修改 `src/ai_classifier.py`：
  - `AIBookmarkClassifier` 加载配置后统一进行分类名规范化（去除 emoji/装饰前缀），避免规则引擎/后续逻辑仍使用带图标分类名。
  - 在融合阶段对各方法返回的 `category` 做规范化，确保最终输出类别不带图标。

- 修改 `src/llm_classifier.py`：
  - 收集可用分类集合时，对 `category_order` / `category_rules` 的分类名进行规范化（去除 emoji/装饰前缀）。
  - LLM 返回分类与本地分类集合对齐时，先做规范化再匹配，避免因 emoji 前缀导致被错误映射为“未分类”。

- 修改 `src/enhanced_cli.py`：
  - 将 `main()` 改为薄封装，直接复用 `CLIInterface().run()`，使 `cleanbook-wizard` 入口与主交互 CLI 收敛到同一实现。

影响：
- 分类结果的主分类/子分类路径不再包含 emoji 图标前缀，内部统计与导出结果一致。
- `cleanbook-wizard` 不再进入 `InteractiveBookmarkManager` 的占位式交互逻辑，避免“模拟/开发中”导致功能不可用。
