# 书签管家 (Bookmark Steward)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/YOUR_USERNAME/clean_bookmark/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/clean_bookmark/actions/workflows/test.yml)

> 您的浏览器书签栏是否杂乱无章？成百上千的链接是否散落各处难以寻找？
>
> **书签管家** 是一款为你解决这些问题的自动化工具。它能将你从 Chrome, Edge, Firefox 等多个浏览器导出的书签文件进行合并，再通过智能分类、清理和去重，转化为一个结构清晰、易于查阅的全新书签库。

<!-- 建议在此处嵌入一个展示脚本运行效果的 GIF 动图 -->
<!-- <p align="center"><img src="docs/demo.gif" width="80%"></p> -->

## ✨ 主要特性

- **合并多个来源**：轻松合并来自 Chrome, Edge, Firefox 等不同浏览器的书签文件。
- **智能分类**：根据自定义关键词，自动将书签归入多级目录（例如 `技术栈/代码 & 开源/GitHub`）。
- **URL 清理**：自动移除 URL 中的跟踪参数（如 `?utm_source=...`），只保留核心链接。
- **链接去重**：在清理后的 URL 基础上进行去重，确保每个链接都是唯一的。
- **特殊处理**：为 GitHub、Docker 等特定网站提供定制化的分类逻辑。
- **域名分组**：可选择性地为某些分类下的书签按域名再做一级细分。
- **双格式输出**：同时生成可重新导入浏览器的 HTML 文件和便于阅读的 Markdown 文件。
- **高度可定制**：通过修改 Python 字典，即可完全自定义您的分类体系。
- **使用简单**：提供清晰的命令行接口，轻松上手。

## ⚙️ 工作原理

书签管家的处理流程如同一条精密的流水线：

1.  **加载配置 (Load Config)**: 解析您通过 `--config` 参数指定的 `config.json` 文件，获取分类规则。
2.  **读取 (Parse)**: 解析您提供的所有 HTML 书签文件，提取出链接和标题。
3.  **清理 (Clean)**: 对每一个 URL 进行"净化"，移除不必要的查询参数和哈希锚点。
4.  **去重 (De-duplicate)**: 基于净化后的 URL，移除所有重复的书签条目。
5.  **分类 (Classify)**: 根据您在脚本中定义的规则，将每一个书签精准地分配到对应的分类或子分类下。
6.  **构建 (Build)**: 将分类好的数据构造成一个层级分明的内存结构。
7.  **输出 (Generate)**: 基于该结构，最终生成清理过的 HTML 和 Markdown 两种格式的文件。


## 📂 项目结构

```
clean_bookmark/
├── src/
│   └── bookmark_cleaner/
│       ├── __init__.py
│       └── main.py          # 核心处理脚本
├── tests/
│   └── test_cleaner.py      # 单元测试
├── examples/
│   ├── bookmarks.html         # 示例：输入的原始书签文件
│   ├── bookmarks_cleaned.html # 示例：脚本生成的已清理 HTML 文件
│   └── bookmarks.md           # 示例：脚本生成的 Markdown 文件
├── .gitignore                 # Git 忽略文件配置
├── LICENSE                    # MIT 许可证
├── requirements.txt           # Python 依赖库
└── README.md                  # 就是您正在看的这个文件
```

## 🚀 安装与使用

### 1. 准备环境

首先，请确保您的电脑已经安装了 Python 3。

然后，克隆本项目到您的本地：
```bash
git clone https://github.com/YOUR_USERNAME/clean_bookmark.git
cd clean_bookmark
```
> **提示**：请将 `YOUR_USERNAME/clean_bookmark` 替换成您自己的仓库地址。

接着，安装所需的依赖库（包括测试工具）：
```bash
pip install -r requirements.txt
```

### 2. 开始整理

该脚本的核心功能是合并与整理。您需要将从各个浏览器导出的书签文件路径作为参数传给脚本。

例如，合并 `examples` 目录下的 `bookmarks.html` 和另一个名为 `edge_bookmarks.html` 的文件：
```bash
# 假设您已将另一个浏览器的书签文件 edge_bookmarks.html 放到了 examples 目录下
python -m bookmark_cleaner.main --input examples/bookmarks.html examples/edge_bookmarks.html
```

脚本执行完毕后，您会在项目根目录下找到两个默认的输出文件：
- `bookmarks_cleaned.html`：已整理好的 **合并后** 的 HTML 文件，可以重新导入到您的浏览器。
- `bookmarks.md`：已整理好的 **合并后** 的 Markdown 文件，方便查阅。

### 3. 命令行选项

您可以通过命令行参数来指定输入和输出文件的路径：

- `-i, --input`: **(必需)** 指定一个或多个输入的 HTML 书签文件，用空格隔开。
- `--output-html`: 指定输出的 HTML 文件路径。默认为 `bookmarks_cleaned.html`。
- `--config`: 指定配置文件路径。

例如，从根目录的 `my_bookmarks.html` 文件进行整理，并将结果输出到 `output` 文件夹：

```bash
# (请先确保 output 文件夹已存在)
python -m bookmark_cleaner.main -i chrome.html edge.html -c my_rules.json --output-html output/cleaned.html
```

## 🛠️ 自定义分类规则

**这是本工具最核心的特性**。您不再需要修改任何 Python 代码，只需编辑 `config.json` 文件，即可创建完全属于您自己的分类体系！

该文件结构如下：

```json
{
  "categories": {
    "AI 研究室": {
      "keywords": [],
      "sub_categories": {
        "对话 & 写作": {
          "keywords": ["chatgpt", "claude", "gemini"]
        }
      }
    }
  },
  "domain_based_subcats": [
    ["AI 研究室", "对话 & 写作"]
  ]
}
```

- **`categories`**: 定义了你的分类层级。
  - `keywords`: 关键词列表，用于匹配 URL 或标题。
  - `sub_categories`: 可选的子分类，可以无限嵌套。
- **`domain_based_subcats`**: 一个列表，其中每个元素 `["主分类", "子分类"]` 表示这个子分类下的书签需要再按域名（如 `github.com`）进行一次细分。

您可以自由地添加、删除、修改这个 JSON 文件来满足您的需求。

## ✅ 运行测试

我们使用 `pytest` 进行单元测试。在安装完依赖后，直接在项目根目录运行：
```bash
pytest
```
您应该能看到所有测试都通过。

## 🤝 如何贡献

我们非常欢迎各种形式的贡献！无论是报告 Bug、提交新功能还是改进文档，都对我们非常有帮助。

- **报告问题**: 如果您发现了 Bug 或者有功能建议，请通过 [Issues](https://github.com/YOUR_USERNAME/clean_bookmark/issues) 提交。
- **提交代码**: 如果您想贡献代码，请遵循以下步骤：
    1. Fork 本仓库。
    2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
    3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)。
    4. 将代码推送到您的分支 (`git push origin feature/AmazingFeature`)。
    5. 打开一个 Pull Request。

## 📜 许可证

本项目采用 [MIT 许可证](LICENSE)。 