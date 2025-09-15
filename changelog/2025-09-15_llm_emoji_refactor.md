# 2025-09-15 重构：LLM 分类接入 + Emoji 预处理 + 去重与导出修复

## 概述
- 新增可选 LLM 分类器（OpenAI 兼容），默认关闭。
- 抽象 `emoji_cleaner.py` 统一清理标题开头指示类 emoji，杜绝导出反复叠加。
- 始终执行高级去重，优化跨浏览器导出文件合并质量。
- 增强导出与增强版处理器的标题清理与层级限制（最多两层）。

## 变更详情
- 新增
  - `src/emoji_cleaner.py`: 提供 `clean_title()`，统一去除开头 emoji（🟢🟡🟠🔴🔥📌⭐❓ 等）。
  - `src/llm_classifier.py`: 通用 LLM 分类器，读取 `config.json.llm`，OpenAI 兼容 API。
- 修改
  - `src/placeholder_modules.py` (DataExporter): 导出 HTML/Markdown 时调用 `clean_title()`，尊重 `show_confidence_indicator`，不再叠加 emoji。
  - `src/bookmark_processor.py`: 读取 HTML 时清理标题 emoji；快速去重后始终执行高级去重。
  - `src/enhanced_clean_tidy.py`: 
    - 使用 `clean_title()`；
    - 生成 HTML/Markdown 前清理标题；
    - 是否显示指示符由 `config.json.show_confidence_indicator` 控制；
    - `organize_bookmarks()` 限制分类层级最多 2 层。
  - `src/ai_classifier.py`、`src/enhanced_classifier.py`: 接入 LLM 分类（可选），纳入融合权重与统计。
  - `config.json`: 新增 `llm` 配置块（默认 `enable=false`）。

## 使用说明
- 运行测试：`python -m pytest -q tests/test_suite.py`
- 处理示例：`python src/enhanced_clean_tidy.py -i examples/demo_bookmarks.html -o tests/output`
- 启用 LLM：在 `config.json` 将 `llm.enable` 置为 `true`，并设置环境变量 `OPENAI_API_KEY`；如使用自建服务，配置 `base_url` 与 `model`。

## 兼容性与注意事项
- 未启用 LLM 时，将完全保持离线行为（兼容原有流程）。
- Emoji 清理仅处理标题起始位置的指示符，不影响正文内容。
- 导出指示符默认关闭（`show_confidence_indicator=false`）。
