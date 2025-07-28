[English](./README_en.md)

# 书签管家 (Bookmark Steward)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个能自动合并、清理和分类浏览器书签的 Python 脚本。
**本项目的核心是一套开放的、由社区驱动的分类规则库 (`config.json`)**，它驱动一个基于权重评分的智能引擎，旨在成为最全面、最合理的书签自动整理方案。

## ✨ 主要特性

- **基于权重的智能评分引擎**：告别简单的关键词匹配！本工具会对书签的域名、URL、标题等信息进行综合评估，为每个可能的分类计算得分，并选择得分最高的分类作为最终归宿，极大提升了分类的准确性和合理性。
- **社区驱动的规则库**：核心 `config.json` 文件开放、可协作。我们鼓励用户贡献规则，共同使其不断进化，覆盖更多领域。
- **多维度分类**：同时根据**内容格式**（视频、文档、代码库）和**内容主题**（技术、设计、新闻）进行精细分类。
- **多策略管理**：支持创建多个 `config_*.json` 策略文件，在运行时按需选择，轻松应对不同场景（如工作、学习、个人）。
- **自动化支持**：从自动合并、去重、URL 清理到最终生成可导入的 `HTML` 和可阅读的 `Markdown` 文件，全程自动化。

## 🚀 快速上手

**只需 3 步，即可体验强大的自动整理。**

1.  **准备项目**：克隆仓库，安装依赖。
    ```bash
    git clone https://github.com/YOUR_USERNAME/CleanBookmarks.git
    cd CleanBookmarks
    pip install -r requirements.txt
    ```
2.  **放入书签**：将您从浏览器导出的 `.html` 书签文件全部放入 `tests/input` 文件夹。
3.  **运行脚本**：
    ```bash
    python src/clean_marks.py
    ```
    脚本将自动使用默认的 `config.json` 规则库。如果检测到多个策略文件，会提示您进行选择。整理好的文件将输出到 `tests/output` 目录。

---

## ❤️ 贡献规则：打造最强大脑

我们相信，最好的分类规则来自成千上万用户的真实需求。贡献规则是本项目最重要的贡献方式，且无需编写任何代码。

**贡献方式**：Fork 本项目 -> 编辑 `config.json` -> 发起 Pull Request。

### 理解规则结构

`config.json` 的核心是 `category_rules`，它定义了主题分类的逻辑。每个分类都由一个 `rules` 数组驱动：

```json
"技术栈/后端 & 数据库": {
    "rules": [
        { 
            "match": "domain", 
            "keywords": ["python.org", "rust-lang.org"], 
            "weight": 10 
        },
        { 
            "match": "title", 
            "keywords": ["python", "golang", "go", "rust"], 
            "weight": 5, 
            "must_not_contain": ["game", "play rust"] 
        },
        { 
            "match": "title", 
            "keywords": [" go "],  // 注意 "go" 两边的空格，用于精确匹配单词
            "weight": 4, 
            "must_not_contain": ["go out", "go shopping"] 
        }
    ]
}
```

- `match`: 指定匹配对象，可以是 `domain` (域名), `url` (完整链接) 或 `title` (标题)。
- `keywords`: 关键词列表。
- `weight`: **权重**。这是智能评分的核心。**域名匹配的权重通常应该最高**，因为它最准确。标题匹配的权重应相对较低。
- `must_not_contain`: **排除词列表**。如果匹配对象中出现了这里的任何一个词，该条规则将不计分。这对于消除歧义至关重要（例如，区分编程语言 `Rust` 和游戏 `Rust`）。

您可以修改现有规则，或仿照此结构添加全新的分类，让我们的"大脑"更聪明！

## 🛠️ 进阶使用：多策略管理

您可以创建多个 `config_*.json` 文件（例如 `config_work.json`, `config_personal.json`），每个文件代表一套独立的分类策略。

当您直接运行脚本时，它会自动检测这些文件，并提供一个菜单让您选择本次要使用的策略（直接回车可选用默认的 `config.json`）。您也可以通过 `--config` 参数强制指定一个配置文件。

## 📜 许可证

本项目采用 [MIT 许可证](LICENSE)。 