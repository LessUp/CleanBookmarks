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

---

## 教学导读

面向第一次接触本项目的读者，本节给出最小心智模型：

- 输入是浏览器导出的 HTML 书签文件，输出是结构化的多格式结果（HTML/Markdown/JSON）。
- 分类遵循“受控词表 + 分面分类 + 权威控制”，并优先规则，模型辅助，可选 LLM 兜底。
- 配置驱动，默认离线可用；不懂代码也能通过 `config.json` 与 `taxonomy/*.yaml` 完成大多数定制。

建议先阅读 `docs/quickstart_zh.md` 完成一次最小运行，再回到本文档理解设计细节。

## 术语速览（KISS）

- `subject`：主题（主维度）。例如：`AI`、`Python`、`Productivity`。
- `resource_type`：资源类型（分面）。例如：`documentation`、`code_repository`、`video`。
- 受控词表（Controlled Vocabulary）：统一首选词与同义变体，避免“同义项四散”。
- 分面分类（Faceted Classification）：按多维属性组织（本项目固定为 `subject -> resource_type`）。
- 权威控制（Authority Control）：词表与映射集中在 YAML 中版本化维护，便于审阅与追踪。

## 5 分钟上手（从 0 到 1）

1. 准备输入：导出浏览器书签 HTML，放到 `examples/` 或自定义路径。
2. 最小执行：
   ```bash
   cleanbook -i examples/demo_bookmarks.html -o output
   ```
3. 查看产出：在 `output/` 下找到 HTML/Markdown/JSON；先看 Markdown 以便人工核验。
4. 若分类不理想：
   - 优先改 `config.json` 的规则与权重。
   - 如需引入 AI：根据 `docs/design/ml_design_zh.md` 训练并集成模型（可选）。
   - 如需启用 LLM：在 `config.json` 打开 `llm.enable` 并设置 Key（可选，支持自动降级）。

## 常见问题（FAQ）

- 如何避免“目录过深/过细”？
  - 保持两级：`subject -> resource_type`。必要时将细项折叠为标签或注释，而非新增层级。

- 标题里的 emoji 重复？
  - 系统在读入/标准化/导出三处均做清理；若仍有问题，请确认使用最新版并检查导出配置。

- 没有网络/不想用云服务？
  - 默认离线可用：规则/词表/ML 训练均可在本地完成；LLM 是可选项，失败会自动降级。

- 如何持续变好？
  - 以“配置优先”方式演进：
    - 新增规则与词表映射，先改 `config.json` 与 `taxonomy/*.yaml`。
    - 将高置信度样本沉淀为训练集，定期训练轻量 ML 模型。

## 设计取舍（Principles）

- 简洁优先（KISS）：接口、数据、流程尽量少而稳定；复杂性留给配置与可选组件。
- 默认可用：无 LLM、无网络、无额外服务也能跑完整流程。
- 可插拔：规则/ML/LLM/导出器均为可选模块，互不强绑定。
- 可追溯：受控词表与配置均在版本库中，配合导出统计与日志，方便回溯与教学。

## 教学建议（用于工作坊/课堂）

- 90 分钟课堂结构：
  - 15 分钟：阅读 `quickstart_zh.md` 并完成最小运行。
  - 30 分钟：基于 `config.json` 新增 3 条规则并演示效果。
  - 30 分钟：构造 30 条标注样本，训练基础 ML 模型并接入。
  - 15 分钟：讨论“受控词表与分面”的优势与边界。

---
