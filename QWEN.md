# Qwen Code 交互定制指南

## 项目概述

AI智能书签分类系统是一个基于人工智能技术的书签管理工具，能够自动分析、分类和组织浏览器书签。

核心组件：
- 规则引擎 (`src/rule_engine.py`) - 基于关键词匹配的快速分类
- 机器学习分类器 (`src/ml_classifier.py`) - 使用scikit-learn进行智能分类
- AI主分类器 (`src/ai_classifier.py`) - 协调多种分类方法的集成系统
- 书签处理器 (`src/bookmark_processor.py`) - 批量处理书签文件
- CLI界面 (`src/cli_interface.py`) - 用户交互界面

## 代码风格约定

1. 遵循PEP8 Python代码规范
2. 使用类型提示（Type Hints）
3. 函数和类需要有完整的文档字符串（docstrings）
4. 重要方法应包含注释说明实现逻辑
5. 配置文件使用JSON格式，保持结构清晰

## 关键实现细节

### 分类器架构
- 使用集成学习方法结合多种分类技术
- 实现了缓存机制优化性能（LRU缓存）
- 支持动态规则添加和权重调整
- 包含置信度评分系统

### 处理流程
1. 解析HTML书签文件
2. 提取书签特征
3. 应用分类规则
4. 机器学习模型预测（如启用）
5. 结果融合和优化
6. 输出多种格式结果文件

### 性能优化
- 多线程并行处理
- 智能缓存策略
- 批处理机制
- 延迟初始化组件

## 配置文件说明

主要配置文件为 `config.json`，包含：
- `category_rules`: 分类规则定义
- `ai_settings`: AI相关设置
- `category_order`: 分类显示顺序
- `title_cleaning_rules`: 标题清理规则

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行健康检查
python src/health_checker.py

# 处理书签（命令行模式）
python main.py -i tests/input/*.html

# 启动交互模式
python main.py --interactive

# 运行测试
python tests/test_suite.py
```

## 输出文件格式

处理完成后生成三种格式的输出文件：
1. HTML格式：可直接导入浏览器
2. JSON格式：包含详细分类信息和统计
3. Markdown格式：可读性强的分类报告

## 重要注意事项

1. 机器学习功能需要安装额外依赖（scikit-learn, jieba等）
2. 大量书签处理时建议调整线程数优化性能
3. 可通过配置文件自定义分类规则和权重
4. 支持中文和英文内容的处理
5. 系统具有学习能力，可根据用户反馈优化分类结果

## 测试策略

项目包含全面的测试套件：
- 单元测试覆盖核心功能
- 集成测试验证组件协同
- 性能测试确保处理效率
- 端到端测试模拟完整流程

运行测试：`python tests/test_suite.py`

## 扩展开发指南

添加新分类方法：
1. 在 `ai_classifier.py` 中实现新分类逻辑
2. 在 `_ensemble_classification` 方法中集成
3. 调整权重配置优化效果
4. 添加相应测试用例