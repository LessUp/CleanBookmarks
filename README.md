# 书签管家 (Bookmark Steward)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个能自动合并、清理和分类浏览器书签的 Python 脚本。
**本项目的核心是一套开放的、由社区驱动的分类规则库 (`config.json`)**，旨在成为最智能、最全面的书签自动整理方案。

## 🚀 快速上手

**只需 3 步，即可整理好您的所有书签。**

**1. 准备项目**

克隆此仓库并进入目录，然后安装依赖：

```bash
git clone https://github.com/YOUR_USERNAME/CleanBookmarks.git
cd CleanBookmarks
pip install -r requirements.txt
```

**2. 放入书签**

将您从 Chrome / Edge / Firefox 等浏览器导出的书签文件（`.html`格式）全部放入 `tests/input` 文件夹。

**3. 运行脚本**

执行以下命令：

```bash
python src/clean&tidy.py
```

脚本运行完毕后，您会在 `tests/output` 目录找到整理好的 `bookmarks_cleaned.html` 和 `bookmarks.md` 文件。

---

## ❤️ 贡献规则：让分类更智能

**我们相信，最好的分类规则来自成千上万用户的真实需求。**

如果您发现某个网站没有被正确分类，或者您希望为某个领域（比如生物、法律、金融）添加新的分类规则，我们非常欢迎您直接贡献！

**贡献方式非常简单：**

1.  **Fork** 本项目。
2.  **编辑** 根目录下的 `config.json` 文件。您可以：
    *   在 `format_rules` 中添加新的视频/文档/工具网站。
    *   在 `categories` 中添加新的主题分类或扩充现有分类的 `keywords` 列表。
3.  **发起 Pull Request**。

您无需编写任何代码，只需修改 `config.json` 这一个文件，就能让这个工具变得更强大。让我们一起打造最完美的书签分类规则库！

## ✨ 主要特性

- **社区驱动的规则库**：核心 `config.json` 文件开放、可协作，不断进化。
- **多维度分类**：同时根据**内容格式**（视频、文档）和**主题**（技术、设计）进行分类。
- **多文件合并**：自动合并所有来源的书签。
- **自动去重 & URL清理**：确保链接的干净与唯一。
- **双格式输出**：同时生成 `HTML` (用于浏览器) 和 `Markdown` (用于阅读) 两种文件。

## 🛠️ 进阶使用

### 多策略管理

您可以创建多个不同的 `config_*.json` 文件（例如 `config_work.json`, `config_simple.json`），每一个文件代表一套独立的分类策略。

当您直接运行 `python src/clean&tidy.py` 时，脚本会自动检测这些文件，并提供一个菜单让您选择本次要使用的策略。

### 命令行参数

您依然可以通过命令行参数来精确控制脚本行为，这在自动化场景下非常有用。

```bash
# 示例：强制使用 'my_rules.json'，并输出到指定位置
python src/clean&tidy.py -c my_rules.json -i ~/Desktop/my_bookmarks.html --output-html D:/cleaned.html
```
- `-i, --input`: 指定一个或多个输入文件。
- `--output-html`: 指定 HTML 输出路径。
- `--output-md`: 指定 Markdown 输出路径。
- `-c, --config`: 指定 `config.json` 配置文件路径。

### 自定义分类

您可以随时修改本地的 `config.json` 文件来添加私有的、不便共享的分类规则。

> **注意**：脚本内置了对 GitHub、常见技术博客（归入"稍后阅读"）等网站的优先分类逻辑，其优先级高于 `config.json` 中的主题分类。

## 📜 许可证

本项目采用 [MIT 许可证](LICENSE)。 