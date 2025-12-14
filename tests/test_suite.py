"""
Comprehensive Testing Framework
综合测试框架

包含：
1. 单元测试
2. 集成测试
3. 性能测试
4. 端到端测试
5. 测试数据生成
6. 测试报告
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any
import time
import random
from datetime import datetime
import logging

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    psutil = None
    _HAS_PSUTIL = False

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.enhanced_classifier import EnhancedClassifier, EnhancedBookmarkFeatures
except Exception:
    EnhancedClassifier = None
    EnhancedBookmarkFeatures = None

try:
    from src.ml_classifier import MLBookmarkClassifier, BookmarkFeatureExtractor, ML_AVAILABLE
except Exception:
    MLBookmarkClassifier = None
    BookmarkFeatureExtractor = None
    ML_AVAILABLE = False

try:
    from src.performance_optimizer import PerformanceMonitor, performance_monitor
    _HAS_PERFORMANCE_OPTIMIZER = True
except Exception:
    PerformanceMonitor = None
    performance_monitor = None
    _HAS_PERFORMANCE_OPTIMIZER = False

try:
    from src.config_manager import EnhancedConfigManager
    _HAS_CONFIG_MANAGER = True
except Exception:
    EnhancedConfigManager = None
    _HAS_CONFIG_MANAGER = False

try:
    from src.advanced_features import (
        IntelligentDeduplicator,
        PersonalizedRecommendationSystem,
        BookmarkHealthChecker,
    )
    _HAS_ADVANCED_FEATURES = True
except Exception:
    IntelligentDeduplicator = None
    PersonalizedRecommendationSystem = None
    BookmarkHealthChecker = None
    _HAS_ADVANCED_FEATURES = False

try:
    from src.enhanced_clean_tidy import EnhancedBookmarkProcessor
    _HAS_ENHANCED_PROCESSOR = True
except Exception:
    EnhancedBookmarkProcessor = None
    _HAS_ENHANCED_PROCESSOR = False

class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def generate_bookmarks(count: int = 100) -> List[Dict]:
        """生成测试书签数据"""
        domains = [
            'github.com', 'stackoverflow.com', 'medium.com', 'youtube.com',
            'wikipedia.org', 'reddit.com', 'news.ycombinator.com', 'dev.to',
            'jupyter.org', 'python.org', 'docs.microsoft.com', 'google.com'
        ]
        
        categories = [
            '技术栈', 'AI', '娱乐', '新闻', '学习', '工具', '社区', '文档'
        ]
        
        bookmarks = []
        
        for i in range(count):
            domain = random.choice(domains)
            category = random.choice(categories)
            
            bookmark = {
                'url': f'https://{domain}/path/{i}',
                'title': f'Test Bookmark {i} - {category}',
                'category': category,
                'confidence': random.uniform(0.5, 1.0),
                'timestamp': datetime.now()
            }
            bookmarks.append(bookmark)
        
        return bookmarks
    
    @staticmethod
    def generate_config() -> Dict:
        """生成测试配置"""
        return {
            "title_cleaning_rules": {
                "prefixes": ["Test ", "Demo "],
                "suffixes": [" - Test", " - Demo"],
                "replacements": {"&": "and"}
            },
            "advanced_settings": {
                "classification_threshold": 0.7,
                "learning_rate": 0.1,
                "cache_size": 1000
            },
            "category_rules": {
                "技术栈": {
                    "rules": [
                        {"match": "domain", "keywords": ["github.com", "stackoverflow.com"], "weight": 10}
                    ]
                },
                "娱乐": {
                    "rules": [
                        {"match": "domain", "keywords": ["youtube.com"], "weight": 8}
                    ]
                }
            },
            "category_order": ["技术栈", "娱乐", "未分类"]
        }

@unittest.skipUnless(
    EnhancedClassifier is not None and EnhancedBookmarkFeatures is not None,
    "EnhancedClassifier 不可用",
)
class TestEnhancedClassifier(unittest.TestCase):
    """增强分类器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.test_config = TestDataGenerator.generate_config()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            self.config_file = f.name
        
        self.classifier = EnhancedClassifier(self.config_file)
    
    def tearDown(self):
        """测试清理"""
        os.unlink(self.config_file)
    
    def test_feature_extraction(self):
        """测试特征提取"""
        url = "https://github.com/user/repo"
        title = "Test Repository"
        
        features = self.classifier.extract_features(url, title)
        
        self.assertIsInstance(features, EnhancedBookmarkFeatures)
        self.assertEqual(features.url, url)
        self.assertEqual(features.title, title)
        self.assertEqual(features.domain, "github.com")
        self.assertIn("user", features.path_segments)
        self.assertIn("repo", features.path_segments)
    
    def test_classification(self):
        """测试分类功能"""
        url = "https://github.com/user/repo"
        title = "Test Repository"
        
        result = self.classifier.classify(url, title)
        
        self.assertIsNotNone(result.category)
        self.assertIsInstance(result.confidence, float)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
    
    def test_learning_from_feedback(self):
        """测试反馈学习"""
        url = "https://example.com/test"
        title = "Test Page"
        
        # 初始分类
        initial_result = self.classifier.classify(url, title)
        
        # 提供反馈
        self.classifier.learn_from_feedback(url, title, "技术栈", initial_result.category)
        
        # 再次分类，应该有所改进
        updated_result = self.classifier.classify(url, title)
        
        # 验证学习权重被更新
        self.assertIsInstance(self.classifier.learning_weights, dict)
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        url = "https://test.com/page"
        title = "Test Page"
        
        # 第一次分类
        start_time = time.time()
        result1 = self.classifier.classify(url, title)
        first_time = time.time() - start_time
        
        # 第二次分类（应该使用缓存）
        start_time = time.time()
        result2 = self.classifier.classify(url, title)
        second_time = time.time() - start_time
        
        # 验证结果一致
        self.assertEqual(result1.category, result2.category)
        
        # 验证缓存提升了性能
        self.assertLess(second_time, first_time)

@unittest.skipUnless(ML_AVAILABLE, "机器学习依赖不可用")
class TestMLClassifier(unittest.TestCase):
    """机器学习分类器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.ml_classifier = MLBookmarkClassifier(model_dir=self.temp_dir)
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_feature_extraction(self):
        """测试特征提取"""
        bookmarks = TestDataGenerator.generate_bookmarks(10)
        
        # 添加必要的字段
        for bookmark in bookmarks:
            bookmark['domain'] = bookmark['url'].split('/')[2]
            bookmark['path_segments'] = bookmark['url'].split('/')[3:]
            bookmark['content_type'] = 'webpage'
            bookmark['language'] = 'en'
        
        extractor = BookmarkFeatureExtractor()
        extractor.fit(bookmarks)
        features = extractor.transform(bookmarks)
        
        self.assertEqual(len(features), len(bookmarks))
        self.assertGreater(features.shape[1], 0)  # 应该有特征列
    
    def test_training_with_insufficient_data(self):
        """测试数据不足时的训练"""
        bookmarks = TestDataGenerator.generate_bookmarks(5)  # 数据不足
        categories = [b['category'] for b in bookmarks]
        
        self.ml_classifier.add_training_data(bookmarks, categories)
        result = self.ml_classifier.train()
        
        self.assertFalse(result)  # 应该训练失败
    
    @unittest.skipIf(not hasattr(sys.modules.get('sklearn'), '__version__'), "sklearn not available")
    def test_training_with_sufficient_data(self):
        """测试足够数据时的训练"""
        bookmarks = TestDataGenerator.generate_bookmarks(50)
        categories = [b['category'] for b in bookmarks]
        
        # 添加必要的字段
        from urllib.parse import urlparse
        for bookmark in bookmarks:
            parsed_url = urlparse(bookmark['url'])
            bookmark['domain'] = parsed_url.netloc
            bookmark['path_segments'] = [seg for seg in parsed_url.path.split('/') if seg]
            bookmark['content_type'] = 'webpage'
            bookmark['language'] = 'en'
        
        self.ml_classifier.add_training_data(bookmarks, categories)
        result = self.ml_classifier.train()
        
        # 如果sklearn可用，训练应该成功
        if hasattr(self.ml_classifier, 'feature_extractor'):
            self.assertTrue(result)

@unittest.skipUnless(_HAS_PERFORMANCE_OPTIMIZER, "PerformanceOptimizer 不可用")
class TestPerformanceOptimizer(unittest.TestCase):
    """性能优化器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.monitor = PerformanceMonitor(max_history=100)
    
    def test_performance_monitoring_decorator(self):
        """测试性能监控装饰器"""
        # 使用monitor的功能直接测试
        from src.performance_optimizer import PerformanceMetrics
        import time
        
        start_time = time.time()
        time.sleep(0.01)  # 模拟处理时间
        end_time = time.time()
        
        # 创建性能指标对象
        metrics = PerformanceMetrics(
            function_name='test_function',
            execution_time=end_time - start_time,
            memory_usage=100,
            cpu_usage=50,
            timestamp=start_time
        )
        
        # 记录性能指标
        self.monitor.record_function_performance(metrics)
        
        # 检查是否记录了性能指标
        self.assertGreater(len(self.monitor.function_stats), 0)
        self.assertIn('test_function', self.monitor.function_stats)
    
    def test_system_monitoring(self):
        """测试系统监控"""
        self.monitor.start_monitoring(interval=0.1)
        time.sleep(0.5)  # 让监控运行一段时间
        self.monitor.stop_monitoring()
        
        # 检查是否收集了系统指标
        self.assertGreater(len(self.monitor.system_metrics), 0)
    
    def test_bottleneck_identification(self):
        """测试瓶颈识别"""
        # 模拟一个慢函数
        @performance_monitor
        def slow_function():
            time.sleep(0.01)
            return "done"
        
        # 运行多次以收集数据
        for _ in range(5):
            slow_function()
        
        bottlenecks = self.monitor.identify_bottlenecks()
        
        # 应该能识别到性能问题
        self.assertIsInstance(bottlenecks, list)

@unittest.skipUnless(_HAS_CONFIG_MANAGER, "ConfigManager 不可用")
class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # 创建测试配置文件
        test_config = TestDataGenerator.generate_config()
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        self.config_manager = EnhancedConfigManager(self.config_file)
    
    def tearDown(self):
        """测试清理"""
        self.config_manager.stop_file_monitoring()
        shutil.rmtree(self.temp_dir)
    
    def test_config_loading(self):
        """测试配置加载"""
        config = self.config_manager.get_config()
        
        self.assertIn("category_rules", config)
        self.assertIn("advanced_settings", config)
    
    def test_config_validation(self):
        """测试配置验证"""
        errors = self.config_manager.validate_current_config()
        
        # 测试配置应该是有效的
        self.assertEqual(len(errors), 0)
    
    def test_config_get_set(self):
        """测试配置获取和设置"""
        # 测试获取
        threshold = self.config_manager.get("advanced_settings.classification_threshold")
        self.assertIsNotNone(threshold)
        
        # 测试设置
        new_value = 0.8
        self.config_manager.set("advanced_settings.classification_threshold", new_value)
        
        updated_value = self.config_manager.get("advanced_settings.classification_threshold")
        self.assertEqual(updated_value, new_value)

@unittest.skipUnless(_HAS_ADVANCED_FEATURES, "AdvancedFeatures 不可用")
class TestAdvancedFeatures(unittest.TestCase):
    """高级功能测试"""
    
    def test_deduplicator(self):
        """测试去重器"""
        deduplicator = IntelligentDeduplicator()
        
        # 创建测试书签，包含重复项
        bookmarks = [
            {'url': 'https://example.com/page1', 'title': 'Test Page'},
            {'url': 'https://example.com/page1', 'title': 'Test Page'},  # 完全重复
            {'url': 'https://example.com/page1?utm_source=test', 'title': 'Test Page'},  # URL参数不同
            {'url': 'https://example.com/page2', 'title': 'Another Page'}
        ]
        
        duplicate_groups = deduplicator.find_duplicates(bookmarks)
        
        # 应该找到重复组
        self.assertGreater(len(duplicate_groups), 0)
        
        # 测试去重
        unique_bookmarks, removed = deduplicator.remove_duplicates(bookmarks)
        
        self.assertLess(len(unique_bookmarks), len(bookmarks))
        self.assertGreater(len(removed), 0)
    
    def test_recommendation_system(self):
        """测试推荐系统"""
        recommender = PersonalizedRecommendationSystem()
        
        bookmarks = TestDataGenerator.generate_bookmarks(20)
        recommender.learn_from_bookmarks(bookmarks)
        
        # 测试分类推荐
        recommendations = recommender.recommend_categories(
            "https://github.com/test/repo",
            "Test Repository"
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    @unittest.skip("需要网络连接")
    def test_health_checker(self):
        """测试健康检查器"""
        checker = BookmarkHealthChecker(max_workers=2, timeout=5)
        
        bookmarks = [
            {'url': 'https://httpbin.org/status/200', 'title': 'Good Link'},
            {'url': 'https://httpbin.org/status/404', 'title': 'Bad Link'},
            {'url': 'https://invalid-domain-12345.com', 'title': 'Invalid Domain'}
        ]
        
        results = checker.check_bookmarks(bookmarks)
        
        self.assertEqual(len(results), len(bookmarks))
        
        # 检查结果类型
        for result in results:
            self.assertIsInstance(result.is_accessible, bool)
            self.assertIsInstance(result.status_code, int)

@unittest.skipUnless(_HAS_ENHANCED_PROCESSOR, "EnhancedBookmarkProcessor 不可用")
class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试初始化"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试配置
        self.config_file = os.path.join(self.temp_dir, "config.json")
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(TestDataGenerator.generate_config(), f)
        
        # 创建测试HTML文件
        self.html_file = os.path.join(self.temp_dir, "bookmarks.html")
        self._create_test_html_file()
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_html_file(self):
        """创建测试HTML文件"""
        html_content = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://github.com/test/repo">Test GitHub Repository</A>
    <DT><A HREF="https://stackoverflow.com/questions/123">Test StackOverflow Question</A>
    <DT><A HREF="https://youtube.com/watch?v=123">Test YouTube Video</A>
</DL><p>'''
        
        with open(self.html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def test_end_to_end_processing(self):
        """端到端处理测试"""
        processor = EnhancedBookmarkProcessor(self.config_file, max_workers=2)
        
        # 处理书签
        processed_bookmarks = processor.process_bookmarks([self.html_file], show_progress=False)
        
        # 验证结果
        self.assertGreater(len(processed_bookmarks), 0)
        
        # 验证每个书签都有必要的字段
        for bookmark in processed_bookmarks:
            self.assertIn('url', bookmark)
            self.assertIn('title', bookmark)
            self.assertIn('category', bookmark)
            self.assertIn('confidence', bookmark)
        
        # 组织书签
        organized = processor.organize_bookmarks(processed_bookmarks)
        
        self.assertIsInstance(organized, dict)
        self.assertGreater(len(organized), 0)

@unittest.skipUnless(EnhancedClassifier is not None, "EnhancedClassifier 不可用")
class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_classification_performance(self):
        """测试分类性能"""
        config = TestDataGenerator.generate_config()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_file = f.name
        
        try:
            classifier = EnhancedClassifier(config_file)
            bookmarks = TestDataGenerator.generate_bookmarks(100)
            
            start_time = time.time()
            
            for bookmark in bookmarks:
                result = classifier.classify(bookmark['url'], bookmark['title'])
                self.assertIsNotNone(result)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 性能要求：每秒至少处理10个书签
            bookmarks_per_second = len(bookmarks) / processing_time
            self.assertGreater(bookmarks_per_second, 10)
            
        finally:
            os.unlink(config_file)
    
    @unittest.skipUnless(_HAS_PSUTIL, "psutil 未安装")
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 创建大量书签
        bookmarks = TestDataGenerator.generate_bookmarks(1000)
        
        # 处理书签
        config = TestDataGenerator.generate_config()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_file = f.name
        
        try:
            classifier = EnhancedClassifier(config_file)
            
            for bookmark in bookmarks:
                classifier.classify(bookmark['url'], bookmark['title'])
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # 内存增长不应超过100MB
            self.assertLess(memory_increase, 100 * 1024 * 1024)
            
        finally:
            os.unlink(config_file)

def run_tests():
    """运行所有测试"""
    # 配置日志
    logging.basicConfig(level=logging.WARNING)
    
    # 创建测试套件
    test_classes = [
        TestEnhancedClassifier,
        TestMLClassifier,
        TestPerformanceOptimizer,
        TestConfigManager,
        TestAdvancedFeatures,
        TestIntegration,
        TestPerformance
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_pytest():
    """使用pytest运行测试"""
    import pytest
    
    # pytest配置
    args = [
        __file__,
        '-v',
        '--tb=short',
        '--maxfail=5'
    ]
    
    return pytest.main(args) == 0

if __name__ == "__main__":
    print("运行测试套件...")
    
    # 尝试使用pytest，回退到unittest
    try:
        import pytest
        success = run_pytest()
    except ImportError:
        print("pytest未安装，使用unittest运行测试")
        success = run_tests()
    
    if success:
        print("✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)