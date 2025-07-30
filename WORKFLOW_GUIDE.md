# AI智能书签分类系统 - 工作流与深度使用指南

本文档为希望深入了解和高效使用“AI智能书签分类系统”的用户提供详细的工作流、配置技巧和开发指导。

## 💡 推荐使用流程 (Recommended Workflow)

为了最大化发挥“规则引擎 + 机器学习”的混合优势，我们强烈建议您遵循以下流程：

### 第 1 步：配置先行，打好基础

- **核心思想**：让规则引擎处理掉“非黑即白”的确定性分类，让机器学习模型专注于“模棱两可”的模糊分类。
- **操作**：
    1.  打开 `config.json` 文件。
    2.  为你最常用、最核心的网站设置明确的 `domain` 规则。例如，将所有 `github.com` 的链接都归类到 `编程`。
    3.  优先定义好大的分类，避免在初期就创建过于细致、样本量可能很少的分类（例如，先用 `学习`，而不是 `学习/书籍手册`）。

### 第 2 步：首次训练，创建个性化模型

- **核心思想**：利用您现有的、已经整理好的书签文件作为“教材”，训练出第一个懂你习惯的AI模型。
- **操作**：
    1.  准备好您的书签导出文件（例如 `my_bookmarks.html`）。该文件的目录结构将被视为“正确答案”。
    2.  运行以下命令进行首次训练：
        ```bash
        python main.py -i my_bookmarks.html --train
        ```
    3.  此命令会做两件事：
        - **立即分类**：使用您刚配好的规则（和可能存在的旧模型）对书签进行分类，并输出结果。
        - **后台训练**：根据您的书签文件，训练一个全新的、更智能的模型，并保存以供未来使用。

### 第 3 步：迭代验证，优化规则

- **核心思想**：检查分类结果，反向优化规则，形成一个正向循环。
- **操作**：
    1.  打开 `output` 文件夹中最新生成的分类报告。
    2.  检查是否有明显的分类错误。
    3.  如果发现错误（例如，某个技术博客被错误分类），**优先考虑是否能通过在 `config.json` 中添加一条新规则来修正它**。这比重新训练模型更高效、更可靠。
    4.  在优化完 `config.json` 后，您可以选择再次运行训练命令来进一步提炼模型。

### 第 4 步：持续使用与再训练

- **核心思想**：随着您的书签不断增加，定期更新模型以适应您的新习惯。
- **操作**：
    - 日常使用时，您可以不带 `--train` 参数，享受快速分类的乐趣。
    - 每隔一段时间（例如一个月，或者收藏了大量新书签后），再次使用 `--train` 参数运行一次，让模型“温故而知新”，保持其高准确率。

遵循以上流程，您将能充分发挥本工具的潜力，打造一个真正属于您的、高效的智能书签系统。

## 📖 详细使用指南

### 交互模式使用

启动交互模式后 (`python main.py --interactive`)，您将看到以下菜单：

```
🚀 AI智能书签分类系统 v2.0

主菜单:
  1: 📂 处理书签文件
  2: 📊 查看处理结果
  3: 🤖 模型管理
  4: 🏥 健康检查
  5: 📈 统计分析
  6: ⚙️ 设置
  h: ❓ 帮助
  q: 🚪 退出
```
通过数字键可以选择不同的功能，这是探索系统所有能力的最佳方式。

### 命令行参数详解

```bash
python main.py [OPTIONS]

选项:
  -i, --input FILES        输入的HTML书签文件 (必须)。可使用通配符，如 "folder/*.html"。
  -o, --output DIR         输出目录 (默认: output)。
  -c, --config FILE        配置文件路径 (默认: config.json)。
  --interactive            启动交互模式。
  --train                  使用输入文件作为训练数据，训练机器学习模型。
  --health-check           运行健康检查，验证环境和配置。
  --workers N              设置用于处理书签的并行线程数 (默认: 4)。
  --threshold FLOAT        分类置信度阈值 (默认: 0.7)。低于此值的分类将被视为“未分类”。
  --no-ml                  完全禁用机器学习功能，仅使用规则引擎。
  --log-level LEVEL        设置日志详细程度 (DEBUG, INFO, WARNING, ERROR)。
```

### 输出文件说明

处理完成后，系统会在输出目录生成以下文件：

- `bookmarks_YYYYMMDD_HHMMSS.html`: 分类整理好的书签文件，可以直接导入回浏览器。
- `bookmarks_YYYYMMDD_HHMMSS.json`: 包含所有书签详细分类信息、置信度等的JSON文件，便于二次开发。
- `report_YYYYMMDD_HHMMSS.md`: Markdown格式的处理报告，包含分类统计、性能指标等信息。

## 🔧 配置 (`config.json`) 详解

### AI设置 (`ai_settings`)

```json
{
  "ai_settings": {
    "confidence_threshold": 0.7,      // 分类置信度阈值
    "use_semantic_analysis": true,    // 是否启用语义分析 (需要额外模型)
    "use_user_profiling": true,       // 是否启用用户画像学习
    "cache_size": 10000,              // 特征和分类结果的缓存条目数
    "max_workers": 4,                 // 并行处理的最大工作线程数
    "enable_learning": true           // 是否启用在线学习和反馈
  }
}
```

### 分类规则 (`category_rules`)

这是系统的核心，定义了规则引擎的行为。

```json
{
  "category_rules": {
    "分类名称": {
      "rules": [
        {
          "match": "domain",                    // 匹配类型: domain/title/url/path
          "keywords": ["github.com"],          // 关键词列表
          "weight": 15,                        // 权重 (1-20)，权重越高的规则越优先
          "must_not_contain": ["game"]         // 排除词 (可选)，如果标题或URL包含这些词，则此规则不生效
        }
      ]
    }
  }
}
```
- **`match` 类型**:
    - `domain`: 匹配书签的域名 (e.g., `github.com`)
    - `title`: 匹配书签的标题
    - `url`: 匹配完整的URL
    - `path`: 匹配URL的路径部分
    - `url_ends_with`: 匹配URL的结尾 (e.g., `.pdf`)

### 分类层次 (`category_hierarchy`)

定义分类之间的父子关系，有助于更好地组织和展示。

```json
{
  "category_hierarchy": {
    "技术": ["编程", "前端", "后端", "DevOps"],
    "AI": ["机器学习", "深度学习", "NLP"],
    "学习": ["教程", "文档", "课程"]
  }
}
```

## 🔬 开发与贡献

### 项目结构

```
CleanBookmarks/
├── main.py                 # 主入口文件
├── config.json            # 配置文件
├── requirements.txt       # 依赖列表
├── src/                   # 源代码目录
│   ├── ai_classifier.py      # AI分类器核心
│   ├── bookmark_processor.py # 书签处理器
│   ├── cli_interface.py      # CLI界面
│   ├── rule_engine.py        # 规则引擎
│   ├── ml_classifier.py      # 机器学习模块
│   └── ...
├── tests/                 # 测试目录
├── models/                # AI模型存储
└── docs/                  # 文档目录
```

### 如何贡献

1.  **Fork & Clone**: Fork项目仓库并克隆到本地。
2.  **安装依赖**: `pip install -r requirements.txt`
3.  **创建分支**: `git checkout -b feature/your-new-feature`
4.  **编码实现**: 添加你的功能或修复。
5.  **测试**: 确保所有测试都能通过 `pytest`。
6.  **提交PR**: 创建一个Pull Request并详细描述你的更改。

---
感谢您花时间阅读这份深度指南！希望它能帮助您更好地使用和参与到这个项目中来。