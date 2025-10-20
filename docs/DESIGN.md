# CleanBookmarks 设计说明

> 目标：以 KISS 原则实现“受控词表 + 分面分类 + 权威控制”的现代化书签分类系统，默认离线可用，可选接入 LLM。

## 架构概览

- 核心流程：`BookmarkProcessor` → 批量加载/去重 → `AIBookmarkClassifier.classify()` → 多方法融合 → 标准化/组织 → 导出
- 多方法融合：规则引擎（RuleEngine）+ 机器学习（可选）+ 语义分析 + 用户画像 + LLM（可选）
- 标准化层：`TaxonomyStandardizer` 基于 `taxonomy/*.yaml` 做受控词表与分面标准化
- 组织逻辑：最终按 `subject -> resource_type` 两级输出，导出时跳过空目录

## 分类原则

- 受控词表（Controlled Vocabulary）：`taxonomy/subjects.yaml` 定义主题首选词与同义变体，避免同义项四散
- 分面分类（Faceted Classification）：
  - 主维度为 `subject`
  - 资源类型分面为 `resource_type`（如 `code_repository`、`documentation`、`video` 等）
  - 规则引擎输出 `facets.resource_type_hint`，与内容类型/域名/URL 关键词共同推断
- 权威控制（Authority Control）：通过 YAML 形式集中维护可扩展的权威表，版本化、审阅友好
- KISS：实现保持简洁，YAML 可读、默认离线、组件可插拔

## 数据与配置

- `taxonomy/subjects.yaml`：
  - `preferred` 为规范主题名
  - `variants` 为同义/近义/别名
- `taxonomy/resource_types.yaml`：
  - 键为规范资源类型枚举（如 `code_repository`）
  - `variants` 为可能出现的别称（如 `github`, `repository`）
- `config.json`：
  - `taxonomy.subjects_file` 与 `taxonomy.resource_types_file` 指向 YAML 文件
  - `ai_settings` 控制各方法启用、缓存、阈值
  - `llm` 为可选启用

## 标准化层（`src/taxonomy_standardizer.py`）

- `normalize_subject(text)`：将任意文本映射到规范主题
- `normalize_resource_type(text)`：将任意文本映射到规范资源类型
- `derive_from_category(category, content_type)`：兼容“主类/子类”旧结构，派生受控 `subject` 与 `resource_type`

## 分类器（`src/ai_classifier.py`）

- 提取特征：域名、路径片段、查询参数、内容类型、语言等
- 方法集成：规则/ML/语义/画像/LLM 的结果融合（加权投票），输出 `ClassificationResult`
- 分面合并：聚合各方法提供的 `facets`（如 `resource_type_hint`）到最终结果
- 缓存与统计：特征与结果缓存、方法使用计数与均值置信度

## 规则引擎（`src/rule_engine.py`）

- 预编译基于 `config.json` 的规则；支持 `domain/title/url/path` 等匹配
- 输出：`category`、`confidence`、`reasoning`、`alternatives`、`method`、`facets`
- 分面提示：基于 `features.content_type`、域名与 URL 关键词推断 `facets.resource_type_hint`

## 组织与导出

- 组织：`BookmarkProcessor._organize_bookmarks()`
  - 主键为 `subject`（标准化）
  - 子键优先使用 `facets.resource_type_hint` → 其次使用 `subcategory` → 再回退内容类型派生
- 导出：`DataExporter`
  - HTML/Markdown/JSON/XML/OPML 多格式
  - 跳过空的 `subject` 与空的 `resource_type` 目录（无 `_items` 时不输出）

## 扩展与演进

- 规则层：在 `config.json` 新增规则/权重即可，无需改代码
- 词表层：维护 YAML 即可扩展主题与资源类型，支持审阅流程
- 统计与可观测性：后续可在导出报告中添加 `subject/resource_type` 分布（Phase 2+）
- 测试建议：对标准化映射与组织逻辑提供最小单元测试

## 简要验收清单

- 旧的分类名均能映射到规范 `subject`
- `resource_type` 能被规则引擎分面或内容类型推断命中
- 导出结果不包含空的分类/子分类目录
- 未配置 LLM 时流程稳定、可回退
