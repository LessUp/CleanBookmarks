# CleanBook 快速上手（中文）

CleanBook 是一个用于清理与分类浏览器书签的命令行工具，支持规则 + 机器学习 + 可选 LLM 分类，默认离线可用。

## 安装与运行

- 推荐方式：pipx（隔离环境、零污染）

```powershell
# 安装 pipx（如未安装）
python -m pip install --user pipx
python -m pipx ensurepath

# 本地安装（开发态）
pipx install .

# 或从源码直接运行
python main.py --help
```

- 两种入口：
  - 命令式处理：`cleanbook`（等价于 `python main.py`）
  - 向导式体验：`cleanbook-wizard`（基于 Rich 的交互式菜单）

## 最小示例

```powershell
# 处理单个书签 HTML 文件
cleanbook -i examples/demo_bookmarks.html -o output

# 批处理多个文件并训练 ML
cleanbook -i "tests/input/*.html" --train

# 交互向导
cleanbook-wizard
```

## 常用参数

- `-i, --input` 输入文件或通配符
- `-o, --output` 输出目录（默认 `output`）
- `--workers` 并行线程数（默认 4）
- `--train` 启用机器学习训练（高置信度样本）
- `--no-ml` 关闭机器学习路径（仅规则/语义/画像）
- `--health-check` 运行链接可达性巡检

## LLM 分类（可选）

默认关闭，严格“可用即用、不可用自动降级”。

1. 打开配置 `config.json`：

```json
"llm": {
  "enable": true,
  "provider": "openai",
  "base_url": "https://api.openai.com",
  "model": "gpt-4o-mini",
  "api_key_env": "OPENAI_API_KEY",
  "temperature": 0.0,
  "top_p": 1.0,
  "timeout_seconds": 25,
  "max_retries": 1
}
```

2. 设置环境变量（Windows PowerShell）：

```powershell
$env:OPENAI_API_KEY = "你的_API_Key"
```

> 未设置 Key 或调用失败时，系统自动回退到离线分类路径。

## 最佳实践（KISS）

- 规则优先、模型辅助、LLM 兜底（可选）。
- 统一标题清理：emoji 前缀由 `src/emoji_cleaner.py` 处理，避免导出叠加。
- 分类层级≤2：增强版组织器限制最多两级，保持结构简洁。
- 去重全时开启：快速去重后总是执行高级去重，合并跨浏览器导出更稳。
- 配置驱动：只改 `config.json` 即可大幅定制行为与目录顺序。

## 产出文件

- HTML：可直接导入浏览器（Netscape 格式）
- Markdown：适合在知识库或代码库中浏览
- JSON：包含统计与明细，可供二次处理

## 故障排查

- 输出标题出现 emoji 叠加？确保使用最新版并确认 `show_confidence_indicator` 配置；系统已在“读入/标准化/导出”三处兜底清理。
- 调用 LLM 无效？检查 `llm.enable` 与环境变量；失败会自动回退。
- 打包安装异常？优先使用 `pipx install .`，或 `python -m pip install .`。
