# AI智能书签分类系统 v2.0

🚀 **一个基于机器学习和规则引擎的智能书签管理工具**

[![license](https://img.shields.io/pypi/l/ansicolortags.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

AI智能书签分类系统能够自动分析、分类和组织您的浏览器书签，将杂乱无章的收藏夹变得井井有条。

## ✨ 核心特性

- 🧠 **AI智能分类**: 结合规则引擎与机器学习，实现精准分类。
- ⚡ **高性能处理**: 支持多线程并行处理，分类速度快。
- 🎯 **个性化模型**: 可通过 `--train` 选项学习您的个人习惯，越用越聪明。
- 🔍 **智能去重**: 自动识别并处理重复的书签。
- 🖥️ **现代化界面**: 提供美观、易用的交互式CLI。
- 🔧 **灵活配置**: 通过 `config.json` 文件高度自定义分类规则。

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-repo/CleanBookmarks.git
cd CleanBookmarks

# 安装依赖
pip install -r requirements.txt
```

### 2. 准备书签文件

将从浏览器导出的书签HTML文件（例如 `bookmarks.html`）放入项目根目录或指定的输入文件夹。

### 3. 开始使用

我们提供了两种模式供您选择：

**A) 交互模式 (推荐新用户)**

此模式提供一个菜单驱动的界面，引导您完成所有操作。

```bash
python main.py --interactive
```

**B) 命令行模式 (适合自动化)**

```bash
# 对单个文件进行分类
python main.py -i tests/input/*.html --workers 32

# 使用通配符处理多个文件，并启用模型训练
python main.py -i "tests/input/*.html" --train
```

---

## 📖 深度使用与工作流

为了充分发挥本工具的潜力，我们为您准备了一份详细的 **[工作流与深度使用指南](WORKFLOW_GUIDE.md)**。

**强烈建议您阅读此指南**，它将帮助您：
-   学习如何通过配置 `config.json` 来打好坚实的分类基础。
-   理解 `--train` 命令背后的工作原理。
-   掌握“规则优先，模型辅助”的最佳实践。
-   打造一个真正符合您个人习惯的、高效的智能书签系统。

[➡️ **点击此处，开始您的深度使用之旅！**](WORKFLOW_GUIDE.md)

---

## 🤝 贡献

我们欢迎任何形式的贡献！无论是提交Bug、建议新功能还是贡献代码，都对项目至关重要。请参考我们的[贡献指南](WORKFLOW_GUIDE.md#如何贡献)。

## 📄 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。