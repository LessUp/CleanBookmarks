# CleanBook —— 智能书签清理与分类（中文）

KISS：规则 + 机器学习 + 可选 LLM，默认离线可用。统一清理标题 emoji，强力去重，输出 HTML/Markdown/JSON。

## 特性

- 规则优先，ML/语义辅助，LLM 可选接入（失败自动降级）。
- 统一标题清理，避免 emoji 前缀叠加。
- 去重全时开启，跨浏览器导出合并更稳。
- 输出分类结构最多两级，结果更简洁。

## 安装（推荐 pipx）

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install .
```

安装后将得到两个命令：

- `cleanbook`：命令式处理（等价于 `python main.py`）
- `cleanbook-wizard`：向导式体验（交互菜单）

## 最小示例

```powershell
cleanbook -i examples/demo_bookmarks.html -o output
cleanbook -i "tests/input/*.html" --train
cleanbook-wizard
```

常用参数：`--workers` 并行，`--train` 训练 ML，`--no-ml` 禁用 ML，`--health-check` 可达性巡检。

## LLM（可选）

编辑 `config.json` 启用：

```json
"llm": {
  "enable": true,
  "provider": "openai",
  "base_url": "https://api.openai.com",
  "model": "gpt-4o-mini",
  "api_key_env": "OPENAI_API_KEY",
  "prompt": {
    "task_description": "请作为 CleanBook-Agent，精确完成浏览器书签分类与信心标注。",
    "steps": [
      "分析书签的标题、URL、域名、关键词，推测主题、意图、受众",
      "从提供的分类库中寻找最合适的主/子类，必要时选择 '未分类'",
      "输出格式化 JSON，包含 category, confidence, reasons, facets 等字段"
    ],
    "scoring_notes": "当存在不确定性时，降低 confidence 并指出疑惑点；若需人工复核，可在 facets.priority_tags 中加入 'review'。",
    "force_json": true
  },
  "organizer": {
    "enable": true,
    "max_examples_per_category": 5,
    "max_domains_per_category": 5,
    "max_tokens": 1800
  }
}
```

然后设置环境变量（PowerShell）：

```powershell
$env:OPENAI_API_KEY = "你的_API_Key"
```

未设置 Key 或失败时自动回退到离线分类。

开启 `organizer.enable` 后，会在分类完成后调用同一套 OpenAI 兼容接口，对书签类别进行二次聚类、排序与总结：

- 自动生成更紧凑的主分类、子分类，并带有洞察说明；
- 失败或未开启时自动回退至传统分类树；
- 统计信息与导出报告会附带 LLM 参与情况，便于复盘。

此外，可通过 `llm.prompt` 定制提示词模板：

- `task_description`：高层任务定义，可结合团队术语；
- `steps`：指引 LLM 按步骤执行（支持多条）；
- `scoring_notes`：补充置信度与复核策略；
- `few_shots`（可选）：提供示例输入/输出，提升对特定类别的识别准确率。

## 目录结构（建议）

```
.
├─ src/
│  ├─ cleanbook/            # 统一 CLI 包装
│  │  └─ cli.py
│  ├─ ai_classifier.py      # 规则+ML+语义+用户画像+LLM(可选)
│  ├─ enhanced_classifier.py
│  ├─ enhanced_clean_tidy.py
│  ├─ bookmark_processor.py
│  ├─ placeholder_modules.py # 导出、占位模块
│  ├─ emoji_cleaner.py       # 标题 emoji 清理
│  └─ ...
├─ models/                  # 模型与缓存
├─ examples/
├─ docs/
│  └─ quickstart_zh.md
├─ config.json
├─ main.py                  # 顶层入口
├─ pyproject.toml           # 打包与命令入口
└─ changelog/
```

不必要的历史/重复文件建议迁入 `legacy/` 或删除（如旧版文档 `doc/` 目录）。

## 发布与分发

- 本地/团队：推荐 `pipx install .`，获得全局命令且环境隔离。
- 开源分发：
  - GitHub 发布源码与 Release 附带示例数据；
  - 可选发布到 PyPI（`python -m build && twine upload dist/*`）。
- Windows 免 Python：可选使用 `PyInstaller` 打包单文件 EXE（进阶）。

更多细节见 `docs/quickstart_zh.md`。

## 许可证

MIT，见 `LICENSE`。
