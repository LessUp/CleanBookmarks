# Gemini Project: AI智能书签分类系统

本文档为 Gemini agent 提供理解和操作此项目所需的上下文信息。

## 1. 项目概述

本项目是一个名为“AI智能书签分类系统”的命令行工具，旨在利用规则引擎和机器学习技术，自动对浏览器书签进行分类和组织。

**核心功能:**
- **智能分类**: 结合关键字规则和机器学习模型，实现对书签的精准分类。
- **高性能处理**: 使用并行处理来加速书签文件的解析和分类过程。
- **重复检测**: 识别并处理重复的书签链接。
- **交互式界面**: 提供一个基于 `rich` 库的用户友好型交互式CLI。
- **灵活配置**: 通过 `config.json` 文件，用户可以自定义分类规则、AI行为和处理流程。

## 2. 技术栈

- **核心语言**: Python 3
- **主要库**:
    - `beautifulsoup4` & `lxml`: 解析HTML书签文件。
    - `scikit-learn` & `jieba`: 用于机器学习文本分类和中文分词。
    - `rich`: 构建丰富的交互式命令行界面。
    - `requests`: 用于书签健康检查（链接可访问性）。
    - `pytest`: 用于单元测试和集成测试。

## 3. 项目结构

以下是项目关键文件和目录的概览：

- **`main.py`**: 应用程序的主入口点，负责解析命令行参数和启动相应的处理流程。
- **`config.json`**: 项目的核心配置文件，定义分类体系、规则和模型设置。
- **`requirements.txt`**: Python依赖项列表。
- **`README.md`**: 包含面向用户的详细项目介绍、安装和使用指南。

- **`src/`**: 存放核心应用逻辑的源代码目录。
    - **`bookmark_processor.py`**: 流程编排器，协调加载、去重、分类和导出等步骤。
    - **`ai_classifier.py`**: AI分类器的主要实现，集成了规则引擎和机器学习。
    - **`rule_engine.py`**: 基于关键字和规则进行分类的引擎。
    - **`ml_classifier.py`**: 基于机器学习模型的分类器。
    - **`cli_interface.py`**: 实现交互式命令行界面。
    - **`health_checker.py`**: 检查书签链接是否有效的模块。
    - **`config_manager.py`**: 负责加载和验证 `config.json`。

- **`tests/`**: 存放测试代码的目录。
    - **`test_suite.py`**: 项目的主要测试套件。
    - **`input/`**: 存放用于测试的输入书签文件。

- **`results/`**: 分类后输出文件的默认存放目录。
- **`models/`**: 存放训练好的机器学习模型的目录。

## 4. 核心工作流

### 4.1. 安装依赖

要安装项目所需的所有Python包，请在项目根目录运行：
```bash
pip install -r requirements.txt
```

### 4.2. 运行应用

应用提供两种运行模式：

**A) 交互模式 (推荐)**
此模式提供一个菜单驱动的界面，方便访问所有功能。
```bash
python main.py --interactive
```

**B) 命令行模式**
此模式适合自动化和脚本调用。
```bash
# 处理单个书签文件
python main.py -i tests/input/demo_bookmarks.html

# 处理多个文件并触发模型训练
python main.py -i "tests/input/*.html" --train
```

### 4.3. 运行测试

项目使用 `pytest` 进行测试。要运行完整的测试套件，请执行：
```bash
pytest
```
或者指定测试文件：
```bash
pytest tests/test_suite.py
```

### 4.4. 健康检查

项目提供了一个健康检查功能，用于验证环境配置和书签链接的有效性。
```bash
python main.py --health-check
```