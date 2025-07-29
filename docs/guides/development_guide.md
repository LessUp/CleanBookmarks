# 开发指南

## 1. 环境搭建

### 1.1 开发环境要求

- **Python**: 3.8+ (推荐 3.9+)
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 最低 4GB, 推荐 8GB+
- **存储**: 最低 2GB 可用空间

### 1.2 开发工具推荐

```bash
# IDE推荐
- VS Code + Python Extension
- PyCharm Professional
- Vim/Neovim + coc.nvim

# 版本控制
- Git 2.20+

# 虚拟环境
- venv (Python内置)
- conda
- poetry
```

### 1.3 项目初始化

```bash
# 克隆项目
git clone <repository-url>
cd CleanBookmarks

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov black flake8 mypy

# 运行健康检查
python src/health_checker.py
```

## 2. 代码结构

### 2.1 目录结构详解

```
CleanBookmarks/
├── main.py                     # 主入口文件
├── config.json                 # 主配置文件
├── requirements.txt            # 生产依赖
├── requirements-dev.txt        # 开发依赖
├── .gitignore                 # Git忽略文件
├── .flake8                    # 代码检查配置
├── pyproject.toml             # 项目配置
├── src/                       # 源代码
│   ├── __init__.py
│   ├── ai_classifier.py           # AI分类器核心
│   ├── bookmark_processor.py      # 书签处理器
│   ├── cli_interface.py          # CLI交互界面
│   ├── rule_engine.py            # 规则引擎
│   ├── ml_classifier.py          # 机器学习模块
│   ├── health_checker.py         # 健康检查
│   └── placeholder_modules.py    # 占位符模块
├── tests/                     # 测试代码
│   ├── __init__.py
│   ├── test_ai_classifier.py     # AI分类器测试
│   ├── test_rule_engine.py       # 规则引擎测试
│   ├── test_processor.py         # 处理器测试
│   ├── input/                    # 测试输入文件
│   └── output/                   # 测试输出文件
├── models/                    # AI模型存储
├── logs/                      # 日志文件
├── docs/                      # 文档
│   ├── api/                      # API文档
│   ├── guides/                   # 使用指南
│   └── design/                   # 设计文档
└── scripts/                   # 脚本工具
    ├── setup.py                  # 安装脚本
    ├── lint.py                   # 代码检查脚本
    └── benchmark.py              # 性能测试脚本
```

### 2.2 代码规范

#### Python代码风格

```python
# 使用类型提示
def classify_bookmark(url: str, title: str) -> ClassificationResult:
    """
    分类单个书签
    
    Args:
        url: 书签URL
        title: 书签标题
        
    Returns:
        分类结果对象
        
    Raises:
        ClassificationError: 分类失败时抛出
    """
    pass

# 使用dataclass
@dataclass
class BookmarkFeatures:
    """书签特征数据类"""
    url: str
    title: str
    domain: str = ""
    confidence: float = 0.0

# 异常处理
try:
    result = classifier.classify(url, title)
except ClassificationError as e:
    logger.error(f"分类失败: {e}")
    raise
except Exception as e:
    logger.error(f"未知错误: {e}")
    return default_result
```

#### 日志规范

```python
import logging

# 日志配置
logger = logging.getLogger(__name__)

# 日志使用
logger.debug("调试信息: 特征提取开始")
logger.info(f"处理完成: {count} 个书签")
logger.warning("配置文件缺少某些字段")
logger.error(f"处理失败: {error_msg}")

# 结构化日志
logger.info("分类完成", extra={
    'bookmark_count': 1000,
    'processing_time': 30.5,
    'accuracy': 0.92
})
```

#### 测试规范

```python
import pytest
from unittest.mock import Mock, patch

class TestAIClassifier:
    """AI分类器测试类"""
    
    def setup_method(self):
        """每个测试方法的初始化"""
        self.classifier = AIClassifier("test_config.json")
    
    def test_classify_github_url(self):
        """测试GitHub URL分类"""
        url = "https://github.com/user/repo"
        title = "Test Repository"
        
        result = self.classifier.classify(url, title)
        
        assert result.category == "技术/代码仓库"
        assert result.confidence > 0.8
        assert "github.com" in result.reasoning[0]
    
    @patch('src.ai_classifier.requests.get')
    def test_classify_with_network_error(self, mock_get):
        """测试网络错误处理"""
        mock_get.side_effect = ConnectionError("Network error")
        
        result = self.classifier.classify("https://example.com", "Test")
        
        assert result.category == "未分类"
        assert result.confidence == 0.0
```

## 3. 核心模块开发

### 3.1 添加新的分类算法

#### 步骤1: 创建分类器类

```python
# src/my_classifier.py
from typing import Optional
from .ai_classifier import ClassificationResult, BookmarkFeatures

class MyCustomClassifier:
    """自定义分类器示例"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model = self._load_model()
    
    def classify(self, features: BookmarkFeatures) -> Optional[ClassificationResult]:
        """实现分类逻辑"""
        try:
            # 你的分类逻辑
            category = self._predict_category(features)
            confidence = self._calculate_confidence(features, category)
            
            return ClassificationResult(
                category=category,
                confidence=confidence,
                reasoning=[f"自定义算法预测: {category}"],
                method="my_custom_classifier"
            )
        except Exception:
            return None
    
    def _predict_category(self, features: BookmarkFeatures) -> str:
        """预测分类"""
        # 实现你的分类算法
        pass
    
    def _calculate_confidence(self, features: BookmarkFeatures, category: str) -> float:
        """计算置信度"""
        # 实现置信度计算
        pass
```

#### 步骤2: 集成到AI分类器

```python
# 在 ai_classifier.py 中添加
from .my_classifier import MyCustomClassifier

class AIBookmarkClassifier:
    def __init__(self, config_path: str, enable_ml: bool = True):
        # ... 现有代码 ...
        
        # 添加自定义分类器
        self.my_classifier = MyCustomClassifier(self.config)
    
    def classify(self, url: str, title: str) -> ClassificationResult:
        # ... 现有代码 ...
        
        # 5. 自定义分类器
        custom_result = self.my_classifier.classify(features)
        if custom_result:
            results.append(custom_result)
        
        # ... 现有代码 ...
```

#### 步骤3: 更新权重配置

```python
# 在 _ensemble_classification 方法中
method_weights = {
    'rule_engine': 0.3,
    'ml_classifier': 0.25,
    'semantic_analyzer': 0.2,
    'user_profiler': 0.1,
    'my_custom_classifier': 0.15  # 新增
}
```

### 3.2 添加新的导出格式

#### 步骤1: 创建导出器

```python
# src/exporters/xml_exporter.py
import xml.etree.ElementTree as ET
from typing import Dict
from ..placeholder_modules import DataExporter

class XMLExporter(DataExporter):
    """XML格式导出器"""
    
    def export(self, organized_bookmarks: Dict, output_file: str, stats: Dict = None):
        """导出XML格式"""
        root = ET.Element("bookmarks")
        root.set("version", "2.0")
        root.set("generator", "AI智能书签分类系统")
        
        # 添加统计信息
        if stats:
            stats_elem = ET.SubElement(root, "statistics")
            for key, value in stats.items():
                stat_elem = ET.SubElement(stats_elem, "stat")
                stat_elem.set("name", key)
                stat_elem.text = str(value)
        
        # 添加书签数据
        bookmarks_elem = ET.SubElement(root, "categories")
        self._add_categories(bookmarks_elem, organized_bookmarks)
        
        # 写入文件
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    def _add_categories(self, parent, data):
        """递归添加分类数据"""
        for category, content in data.items():
            category_elem = ET.SubElement(parent, "category")
            category_elem.set("name", category)
            
            # 添加书签项目
            if '_items' in content:
                for item in content['_items']:
                    bookmark_elem = ET.SubElement(category_elem, "bookmark")
                    bookmark_elem.set("url", item['url'])
                    bookmark_elem.set("confidence", str(item.get('confidence', 0)))
                    bookmark_elem.text = item['title']
            
            # 递归处理子分类
            subcategories = {k: v for k, v in content.items() if k != '_items'}
            if subcategories:
                sub_elem = ET.SubElement(category_elem, "subcategories") 
                self._add_categories(sub_elem, subcategories)
```

#### 步骤2: 注册导出器

```python
# 在 bookmark_processor.py 中
from .exporters.xml_exporter import XMLExporter

class BookmarkProcessor:
    def __init__(self, ...):
        # ... 现有代码 ...
        self.exporters = {
            'html': self.exporter.export_html,
            'json': self.exporter.export_json,
            'markdown': self.exporter.export_markdown,
            'xml': XMLExporter().export  # 新增
        }
    
    def _export_results(self, organized_bookmarks: Dict, output_dir: str):
        """导出处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出所有格式
        for format_name, exporter in self.exporters.items():
            output_file = os.path.join(output_dir, f"bookmarks_{timestamp}.{format_name}")
            exporter(organized_bookmarks, output_file, self.stats)
```

### 3.3 添加新的规则类型

#### 步骤1: 扩展规则引擎

```python
# 在 rule_engine.py 中添加新的匹配器
def _match_content_analysis(target_str, rule, bookmark_context):
    """基于内容分析的匹配器"""
    keywords = rule.get("keywords", [])
    analysis_type = rule.get("analysis_type", "keyword_density")
    
    if analysis_type == "keyword_density":
        # 计算关键词密度
        text = bookmark_context.get("title", "") + " " + bookmark_context.get("domain", "")
        word_count = len(text.split())
        
        if word_count == 0:
            return False
        
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text.lower())
        density = keyword_matches / word_count
        
        threshold = rule.get("density_threshold", 0.1)
        return density >= threshold
    
    elif analysis_type == "semantic_similarity":
        # 语义相似度匹配 (占位符)
        return False
    
    return False

# 更新匹配器调度表
MATCHER_DISPATCHER = {
    "domain": _match_simple_lookup,
    "url": _match_simple_lookup,
    "title": _match_simple_lookup,
    "url_starts_with": _match_url_starts_with,
    "url_ends_with": _match_url_ends_with,
    "url_matches_regex": _match_url_matches_regex,
    "content_analysis": _match_content_analysis,  # 新增
}
```

#### 步骤2: 配置示例

```json
{
  "category_rules": {
    "AI/深度学习": {
      "rules": [
        {
          "match": "content_analysis",
          "analysis_type": "keyword_density",
          "keywords": ["neural", "deep", "learning", "AI"],
          "density_threshold": 0.15,
          "weight": 12
        }
      ]
    }
  }
}
```

## 4. 测试开发

### 4.1 单元测试编写

```python
# tests/test_rule_engine.py
import pytest
from src.rule_engine import RuleEngine
from src.ai_classifier import BookmarkFeatures

class TestRuleEngine:
    """规则引擎测试"""
    
    @pytest.fixture
    def rule_engine(self):
        """测试夹具"""
        config = {
            "category_rules": {
                "技术/编程": {
                    "rules": [
                        {
                            "match": "domain",
                            "keywords": ["github.com", "stackoverflow.com"],
                            "weight": 15
                        }
                    ]
                }
            }
        }
        return RuleEngine(config)
    
    @pytest.fixture  
    def sample_features(self):
        """示例特征"""
        return BookmarkFeatures(
            url="https://github.com/user/repo",
            title="Test Repository",
            domain="github.com",
            path_segments=["user", "repo"],
            query_params={},
            content_type="code_repository",
            language="en"
        )
    
    def test_github_classification(self, rule_engine, sample_features):
        """测试GitHub分类"""
        result = rule_engine.classify(sample_features)
        
        assert result is not None
        assert result['category'] == "技术/编程"
        assert result['confidence'] > 0.8
        assert "github.com" in str(result['reasoning'])
    
    def test_no_match(self, rule_engine):
        """测试无匹配情况"""
        features = BookmarkFeatures(
            url="https://example.com",
            title="Random Page",
            domain="example.com",
            path_segments=[],
            query_params={},
            content_type="webpage",
            language="en"
        )
        
        result = rule_engine.classify(features)
        assert result is None
    
    @pytest.mark.parametrize("domain,expected", [
        ("github.com", "技术/编程"),
        ("stackoverflow.com", "技术/编程"),
        ("example.com", None)
    ])
    def test_domain_classification(self, rule_engine, domain, expected):
        """参数化测试域名分类"""
        features = BookmarkFeatures(
            url=f"https://{domain}",
            title="Test",
            domain=domain,
            path_segments=[],
            query_params={},
            content_type="webpage", 
            language="en"
        )
        
        result = rule_engine.classify(features)
        
        if expected:
            assert result['category'] == expected
        else:
            assert result is None
```

### 4.2 集成测试

```python
# tests/test_integration.py
import tempfile
import json
from src.bookmark_processor import BookmarkProcessor

class TestIntegration:
    """集成测试"""
    
    def test_end_to_end_processing(self):
        """端到端处理测试"""
        # 创建临时配置文件
        config = {
            "ai_settings": {"confidence_threshold": 0.5},
            "category_rules": {
                "技术": {
                    "rules": [{"match": "domain", "keywords": ["github.com"], "weight": 10}]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_file = f.name
        
        # 创建临时HTML文件
        html_content = '''
        <!DOCTYPE NETSCAPE-Bookmark-file-1>
        <TITLE>Bookmarks</TITLE>
        <H1>Bookmarks</H1>
        <DL><p>
            <DT><A HREF="https://github.com/user/repo">Test Repository</A>
        </DL><p>
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            html_file = f.name
        
        # 处理书签
        processor = BookmarkProcessor(config_path=config_file, use_ml=False)
        
        with tempfile.TemporaryDirectory() as output_dir:
            stats = processor.process_files([html_file], output_dir)
            
            # 验证结果
            assert stats['processed_bookmarks'] == 1
            assert stats['total_bookmarks'] == 1
            assert '技术' in stats['categories_found']
            
            # 检查输出文件
            import os
            output_files = os.listdir(output_dir)
            assert any(f.endswith('.html') for f in output_files)
            assert any(f.endswith('.json') for f in output_files)
```

### 4.3 性能测试

```python
# tests/test_performance.py
import time
import pytest
from src.ai_classifier import AIClassifier

class TestPerformance:
    """性能测试"""
    
    @pytest.mark.performance
    def test_classification_speed(self):
        """测试分类速度"""
        classifier = AIClassifier("config.json")
        
        # 测试数据
        test_bookmarks = [
            ("https://github.com/user/repo1", "Repository 1"),
            ("https://stackoverflow.com/questions/123", "Question 123"),
            ("https://youtube.com/watch?v=abc", "Video ABC")
        ] * 100  # 300个书签
        
        start_time = time.time()
        
        for url, title in test_bookmarks:
            result = classifier.classify(url, title)
            assert result.category is not None
        
        end_time = time.time()
        processing_time = end_time - start_time
        speed = len(test_bookmarks) / processing_time
        
        # 性能要求: 至少20书签/秒
        assert speed >= 20, f"处理速度太慢: {speed:.2f} 书签/秒"
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        classifier = AIClassifier("config.json")
        
        # 处理大量书签
        for i in range(1000):
            classifier.classify(f"https://example{i}.com", f"Title {i}")
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应少于100MB
        assert memory_increase < 100 * 1024 * 1024, f"内存使用过多: {memory_increase / 1024 / 1024:.2f}MB"
```

### 4.4 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_rule_engine.py

# 运行带覆盖率的测试
pytest --cov=src --cov-report=html

# 运行性能测试
pytest -m performance

# 运行测试并生成详细报告
pytest -v --tb=short

# 并行运行测试
pytest -n auto
```

## 5. 调试和性能优化

### 5.1 调试技巧

#### 启用调试模式

```python
# 在 main.py 中
import logging

# 设置调试级别
logging.basicConfig(level=logging.DEBUG)

# 或在运行时指定
python main.py --log-level DEBUG
```

#### 使用调试器

```python
# 在代码中设置断点
import pdb; pdb.set_trace()

# 或使用更好的调试器
import ipdb; ipdb.set_trace()

# VS Code调试配置 (.vscode/launch.json)
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--interactive"],
            "console": "integratedTerminal"
        }
    ]
}
```

#### 性能分析

```python
# 使用cProfile
python -m cProfile -o profile_output.prof main.py -i input.html

# 分析结果
python -c "import pstats; pstats.Stats('profile_output.prof').sort_stats('cumulative').print_stats(20)"

# 使用line_profiler
@profile  # 需要安装kernprof
def classify_bookmark(self, url, title):
    # 函数代码
    pass

# 运行
kernprof -l -v main.py
```

### 5.2 性能优化指南

#### 缓存优化

```python
from functools import lru_cache

class Optimizer:
    @lru_cache(maxsize=10000)
    def _parse_url_cached(self, url: str):
        """缓存URL解析结果"""
        return urlparse(url)
    
    def optimize_feature_extraction(self, urls: List[str]):
        """批量特征提取优化"""
        # 预处理URL
        parsed_urls = {url: self._parse_url_cached(url) for url in urls}
        
        # 批量处理
        return [self._extract_features_fast(url, parsed_urls[url]) for url in urls]
```

#### 内存优化

```python
import gc
from typing import Iterator

class MemoryOptimizer:
    def process_bookmarks_streaming(self, bookmarks: Iterator) -> Iterator:
        """流式处理节省内存"""
        batch_size = 100
        batch = []
        
        for bookmark in bookmarks:
            batch.append(bookmark)
            
            if len(batch) >= batch_size:
                yield from self._process_batch(batch)
                batch.clear()
                gc.collect()  # 强制垃圾回收
        
        if batch:
            yield from self._process_batch(batch)
```

#### 并行优化

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

class ParallelProcessor:
    def __init__(self):
        self.cpu_count = mp.cpu_count()
    
    def process_parallel(self, bookmarks: List, chunk_size: int = None):
        """进程池并行处理"""
        if chunk_size is None:
            chunk_size = len(bookmarks) // self.cpu_count
        
        chunks = [bookmarks[i:i+chunk_size] for i in range(0, len(bookmarks), chunk_size)]
        
        with ProcessPoolExecutor(max_workers=self.cpu_count) as executor:
            results = list(executor.map(self._process_chunk, chunks))
        
        return [item for chunk_result in results for item in chunk_result]
```

## 6. 部署和发布

### 6.1 打包发布

```bash
# 创建发布包
python setup.py sdist bdist_wheel

# 上传到PyPI (测试)
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# 上传到PyPI (正式)
twine upload dist/*
```

### 6.2 Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python src/health_checker.py || exit 1

# 启动命令
CMD ["python", "main.py", "--interactive"]
```

```bash
# 构建镜像
docker build -t ai-bookmark-classifier:v2.0 .

# 运行容器
docker run -it -v $(pwd)/data:/app/data ai-bookmark-classifier:v2.0

# 使用docker-compose
docker-compose up -d
```

### 6.3 CI/CD配置

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 src tests --max-line-length=100
    
    - name: Type check with mypy
      run: |
        mypy src
    
    - name: Test with pytest
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t ai-bookmark-classifier:latest .
    
    - name: Run health check
      run: |
        docker run --rm ai-bookmark-classifier:latest python src/health_checker.py
```

这个开发指南涵盖了从环境搭建到部署发布的完整开发流程，为开发者提供了详细的技术指导和最佳实践。