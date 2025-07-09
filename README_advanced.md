# 🚀 高级智能书签分类系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

一个基于机器学习和语义分析的高级书签分类系统，能够智能理解书签内容并自动分类整理。

## ✨ 核心特性

### 🧠 智能分类引擎
- **多层次分类算法**: 结合规则匹配、语义分析、机器学习和自适应学习
- **语义理解**: 基于TF-IDF和余弦相似度的语义匹配
- **多语言支持**: 支持中英文混合内容的智能分析
- **置信度评估**: 为每个分类提供置信度评分

### 🔄 自适应学习系统
- **用户反馈学习**: 从用户纠正中学习，持续改进分类准确性
- **动态权重调整**: 根据历史分类效果自动调整规则权重
- **个性化分类**: 根据用户使用习惯优化分类策略
- **增量学习**: 支持在线学习，无需重新训练

### 🔍 智能重复检测
- **多维度去重**: URL标准化、内容哈希、语义相似度
- **模糊匹配**: 识别参数不同但内容相同的重复链接
- **智能合并**: 自动合并相似书签，保留最佳版本

### 💡 增强用户体验
- **交互式分类**: 实时收集用户反馈，提升分类准确性
- **置信度可视化**: 清晰显示分类的可信程度
- **详细统计报告**: 全面的分类效果分析和改进建议
- **渐进式优化**: 使用越多，效果越好

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/CleanBookmarks.git
cd CleanBookmarks

# 安装依赖
pip install -r requirements_advanced.txt

# 创建必要目录
mkdir -p models tests/input tests/output
```

### 2. 基础使用

```bash
# 将书签HTML文件放入 tests/input/ 目录
# 运行高级分类系统
python src/advanced_clean_tidy.py

# 使用自定义配置
python src/advanced_clean_tidy.py -c config_advanced.json
```

### 3. 交互式模式（推荐）

```bash
# 启用交互式反馈，系统会在不确定时询问您的意见
python src/advanced_clean_tidy.py --interactive

# 查看分类统计
python src/advanced_clean_tidy.py --stats
```

## 🎯 高级功能

### 智能分类算法

系统采用**四层分类架构**：

1. **规则层**: 基于域名、URL、标题的精确匹配
2. **语义层**: 使用TF-IDF向量化和余弦相似度
3. **机器学习层**: 基于历史数据的监督学习
4. **自适应层**: 从用户反馈中持续学习

### 分类置信度系统

- **🔥 高置信度 (>0.8)**: 系统非常确定的分类
- **📌 中置信度 (0.6-0.8)**: 合理的分类，可能需要用户确认
- **❓ 低置信度 (<0.6)**: 需要用户反馈的分类

### 自适应学习机制

```python
# 系统会自动记录用户反馈并调整分类策略
def learn_from_feedback(url, suggested_category, actual_category):
    # 1. 更新分类权重
    # 2. 提取新的分类模式
    # 3. 优化相似度计算
    # 4. 持久化学习结果
```

## 📊 配置说明

### 高级配置项

```json
{
  "advanced_settings": {
    "classification_threshold": 0.6,        // 分类置信度阈值
    "semantic_similarity_threshold": 0.7,   // 语义相似度阈值
    "learning_rate": 0.1,                   // 学习率
    "adaptive_learning_enabled": true,      // 启用自适应学习
    "multi_language_support": true          // 多语言支持
  }
}
```

### 语义规则配置

```json
{
  "semantic_rules": {
    "programming_keywords": {
      "chinese": ["编程", "开发", "代码"],
      "english": ["programming", "development", "coding"]
    }
  }
}
```

## 🔧 API使用

### 基础API

```python
from advanced_classifier import AdvancedBookmarkClassifier

# 初始化分类器
classifier = AdvancedBookmarkClassifier("config_advanced.json")

# 分类单个书签
result = classifier.classify_bookmark(
    url="https://github.com/pytorch/pytorch",
    title="PyTorch: An open source machine learning framework"
)

print(f"分类: {result.category}")
print(f"置信度: {result.confidence:.2f}")
print(f"备选分类: {result.alternative_categories}")
```

### 用户反馈API

```python
# 添加用户反馈
classifier.add_user_feedback(
    url="https://example.com",
    suggested_category="技术文档",
    actual_category="AI & 机器学习/教程",
    confidence=0.75
)

# 获取学习统计
stats = classifier.get_statistics()
print(f"准确率: {stats['accuracy']:.2f}")
```

## 📈 性能优化

### 内存优化
- **LRU缓存**: 缓存URL解析结果
- **批处理**: 支持大批量书签处理
- **增量更新**: 只处理新增或修改的书签

### 速度优化
- **并行处理**: 支持多线程分类
- **索引优化**: 快速查找历史分类结果
- **懒加载**: 按需加载机器学习模型

## 🧪 测试和验证

### 分类准确性测试

```bash
# 运行测试套件
python -m pytest tests/

# 基准测试
python tests/benchmark.py
```

### 人工验证

1. 使用 `--interactive` 模式进行人工标注
2. 系统会自动计算和显示准确率
3. 生成详细的分类报告

## 🔮 未来计划

### 短期目标
- [ ] 集成更多机器学习模型
- [ ] 支持内容抓取和分析
- [ ] 增加更多语言支持
- [ ] 优化用户界面

### 长期目标
- [ ] 基于BERT的深度语义理解
- [ ] 联邦学习支持
- [ ] 浏览器插件集成
- [ ] 云端同步功能

## 🤝 贡献指南

我们欢迎所有形式的贡献：

1. **改进分类规则**: 编辑 `config_advanced.json`
2. **优化算法**: 提交算法改进的PR
3. **添加测试**: 增加测试用例和基准测试
4. **文档完善**: 改进使用文档和API文档

## 📜 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

感谢所有贡献者和以下开源项目：
- [scikit-learn](https://scikit-learn.org/) - 机器学习库
- [jieba](https://github.com/fxsjy/jieba) - 中文分词
- [langdetect](https://github.com/Mimino666/langdetect) - 语言检测
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML解析

---

**使用愉快！如果这个项目对您有帮助，请给我们一个 ⭐️**