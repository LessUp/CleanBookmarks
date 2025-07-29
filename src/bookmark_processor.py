"""
Bookmark Processor - 书签处理器

负责批量处理书签文件，协调各个组件完成整个分类流程
"""

import json
import logging
import os
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from bs4 import BeautifulSoup
from .ai_classifier import AIBookmarkClassifier

# 导入占位符模块
from .placeholder_modules import (
    DataExporter, BookmarkDeduplicator, HealthChecker
)

class BookmarkProcessor:
    """书签处理器主类"""
    
    def __init__(self, config_path: str = "config.json", max_workers: int = 4, use_ml: bool = True):
        self.config_path = config_path
        # 优化线程池大小：限制最大线程数避免过度竞争
        self.max_workers = min(max_workers, 32)  # 限制最大32线程
        self.use_ml = use_ml
        
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"无法加载或解析配置文件 {config_path}: {e}")
            self.config = {}

        # 延迟初始化组件以避免启动开销
        self._classifier = None
        self._deduplicator = None
        self._health_checker = None
        self._exporter = None
        
        # 缓存和性能优化
        self._classification_cache = {}
        self._url_validation_cache = {}
        
        # 处理统计
        self.stats = {
            'total_bookmarks': 0,
            'processed_bookmarks': 0,
            'duplicates_removed': 0,
            'errors': 0,
            'processing_time': 0.0,
            'categories_found': {},
            'files_processed': 0
        }
    
    @property
    def classifier(self):
        """Lazy loading classifier"""
        if self._classifier is None:
            self._classifier = AIBookmarkClassifier(self.config_path, enable_ml=self.use_ml)
        return self._classifier
    
    @property
    def deduplicator(self):
        """Lazy loading deduplicator"""
        if self._deduplicator is None:
            from .placeholder_modules import BookmarkDeduplicator
            self._deduplicator = BookmarkDeduplicator()
        return self._deduplicator
    
    @property
    def health_checker(self):
        """Lazy loading health checker"""
        if self._health_checker is None:
            from .placeholder_modules import HealthChecker
            self._health_checker = HealthChecker()
        return self._health_checker
    
    @property
    def exporter(self):
        """Lazy loading exporter"""
        if self._exporter is None:
            from .placeholder_modules import DataExporter
            self._exporter = DataExporter(config=self.config)
        return self._exporter
    
    def process_files(self, input_files: List[str], output_dir: str = "output", 
                     train_models: bool = False) -> Dict:
        """处理多个书签文件"""
        start_time = time.time()
        
        self.logger.info(f"开始处理 {len(input_files)} 个文件")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 并行加载所有书签以加速IO操作
        all_bookmarks = []
        with ThreadPoolExecutor(max_workers=min(len(input_files), 8)) as file_executor:
            file_futures = {file_executor.submit(self._load_bookmarks_from_file, file_path): file_path 
                          for file_path in input_files}
            
            for future in as_completed(file_futures):
                file_path = file_futures[future]
                try:
                    bookmarks = future.result()
                    all_bookmarks.extend(bookmarks)
                    self.stats['files_processed'] += 1
                except Exception as e:
                    self.logger.error(f"加载文件失败 {file_path}: {e}")
                    self.stats['errors'] += 1
        
        self.stats['total_bookmarks'] = len(all_bookmarks)
        
        if not all_bookmarks:
            self.logger.warning("没有找到有效的书签")
            return self.stats
        
        # 优化去重处理：先进行快速URL去重
        self.logger.info("开始快速去重处理...")
        # 快速URL去重
        seen_urls = set()
        fast_unique = []
        for bookmark in all_bookmarks:
            url = bookmark.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                fast_unique.append(bookmark)
        
        fast_duplicates_removed = len(all_bookmarks) - len(fast_unique)
        self.logger.info(f"快速去重移除了 {fast_duplicates_removed} 个重复书签")
        
        # 对剩余书签进行高级去重
        if len(fast_unique) > 1000:  # 只对大量书签进行高级去重
            unique_bookmarks, duplicates = self.deduplicator.remove_duplicates(fast_unique)
            self.stats['duplicates_removed'] = fast_duplicates_removed + len(duplicates)
        else:
            unique_bookmarks = fast_unique
            self.stats['duplicates_removed'] = fast_duplicates_removed
        
        # 并行分类处理
        self.logger.info(f"开始分类 {len(unique_bookmarks)} 个书签...")
        classified_bookmarks = self._classify_bookmarks_parallel(unique_bookmarks)
        
        # 组织分类结果
        organized_bookmarks = self._organize_bookmarks(classified_bookmarks)
        
        # 导出结果
        self._export_results(organized_bookmarks, output_dir)
        
        # 训练模型（如果启用）
        if train_models and self.use_ml:
            self._train_models(classified_bookmarks)
        
        # 更新统计
        self.stats['processing_time'] = time.time() - start_time
        self.stats['processed_bookmarks'] = len(classified_bookmarks)
        
        self.logger.info(f"处理完成: {self.stats['processed_bookmarks']} 个书签已分类")
        
        return self.stats
    
    def _load_bookmarks_from_file(self, file_path: str) -> List[Dict]:
        """优化的从HTML文件加载书签"""
        bookmarks = []
        
        try:
            # 使用更快的解析器
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用lxml解析器如果可用，否则使用html.parser
            try:
                soup = BeautifulSoup(content, 'lxml')
            except:
                soup = BeautifulSoup(content, 'html.parser')
            
            links = soup.find_all('a', href=True)  # 只查找有href的链接
            
            for link in links:
                url = link.get('href', '').strip()
                title = (link.string or link.get_text() or '').strip()
                
                if url and title and self._is_valid_url(url):
                    bookmarks.append({
                        'url': url,
                        'title': title,
                        'source_file': file_path,
                        'add_date': link.get('add_date', ''),
                        'last_modified': link.get('last_modified', '')
                    })
            
            self.logger.info(f"从 {file_path} 加载了 {len(bookmarks)} 个书签")
            
        except Exception as e:
            self.logger.error(f"加载文件失败 {file_path}: {e}")
            self.stats['errors'] += 1
        
        return bookmarks
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL有效性"""
        if not url:
            return False
        
        # 过滤无效URL
        invalid_prefixes = ['javascript:', 'data:', 'chrome:', 'about:', 'file:', 'mailto:']
        for prefix in invalid_prefixes:
            if url.lower().startswith(prefix):
                return False
        
        return url.startswith(('http://', 'https://'))
    
    def _classify_bookmarks_parallel(self, bookmarks: List[Dict]) -> List[Dict]:
        """优化的并行分类书签"""
        classified_bookmarks = []
        batch_size = 100  # 批处理大小
        
        # 分批处理以减少内存使用和提高效率
        for i in range(0, len(bookmarks), batch_size):
            batch = bookmarks[i:i + batch_size]
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交分类任务
                future_to_bookmark = {
                    executor.submit(self._classify_single_bookmark_cached, bookmark): bookmark
                    for bookmark in batch
                }
                
                # 收集结果
                batch_results = []
                for future in as_completed(future_to_bookmark):
                    bookmark = future_to_bookmark[future]
                    
                    try:
                        result = future.result(timeout=30)  # 添加超时
                        if result:
                            batch_results.append(result)
                            
                    except Exception as e:
                        self.logger.error(f"分类失败 {bookmark.get('url', 'unknown')}: {e}")
                        self.stats['errors'] += 1
                
                classified_bookmarks.extend(batch_results)
                
                # 显示进度
                completed = i + len(batch)
                progress = min(completed / len(bookmarks) * 100, 100)
                self.logger.info(f"分类进度: {progress:.1f}% ({completed}/{len(bookmarks)})")
        
        return classified_bookmarks
    
    def _classify_single_bookmark_cached(self, bookmark: Dict) -> Optional[Dict]:
        """带缓存的单个书签分类"""
        try:
            url = bookmark['url']
            title = bookmark['title']
            
            # 创建缓存键
            cache_key = f"{url}|{title}"
            
            # 检查缓存
            if cache_key in self._classification_cache:
                cached_result = self._classification_cache[cache_key]
                return {
                    **bookmark,
                    **cached_result
                }
            
            # 使用AI分类器
            result = self.classifier.classify(url, title)
            
            # 处理分类结果（可能是对象或字典）
            if hasattr(result, 'category'):
                # ClassificationResult对象
                cached_data = {
                    'category': result.category,
                    'subcategory': result.subcategory if hasattr(result, 'subcategory') else None,
                    'confidence': result.confidence,
                    'alternatives': result.alternatives if hasattr(result, 'alternatives') else [],
                    'reasoning': result.reasoning if hasattr(result, 'reasoning') else [],
                    'method': result.method if hasattr(result, 'method') else 'unknown',
                    'processing_time': result.processing_time if hasattr(result, 'processing_time') else 0.0
                }
            else:
                # 字典结果
                cached_data = {
                    'category': result.get('category', '未分类'),
                    'subcategory': result.get('subcategory'),
                    'confidence': result.get('confidence', 0.0),
                    'alternatives': result.get('alternatives', []),
                    'reasoning': result.get('reasoning', []),
                    'method': result.get('method', 'unknown'),
                    'processing_time': result.get('processing_time', 0.0)
                }
            
            # 限制缓存大小
            if len(self._classification_cache) < 10000:
                self._classification_cache[cache_key] = cached_data
            
            # 构建结果
            classified_bookmark = {
                **bookmark,
                **cached_data
            }
            
            # 更新分类统计
            category = cached_data['category']
            self.stats['categories_found'][category] = self.stats['categories_found'].get(category, 0) + 1
            
            return classified_bookmark
            
        except Exception as e:
            self.logger.error(f"单个书签分类失败: {e}")
            return None
    
    def _organize_bookmarks(self, classified_bookmarks: List[Dict]) -> Dict:
        """组织书签为层次结构"""
        organized = {}
        
        # 分类名称标准化映射
        category_mapping = {
            'AI': '🤖 AI',
            'AI/模型与平台': '🤖 AI/模型平台',
            'AI/应用与工具': '🤖 AI/应用工具', 
            'AI/论文与资讯': '🤖 AI/论文资讯',
            '技术栈': '💻 编程',
            '技术栈/代码 & 开源': '💻 编程/代码仓库',
            '技术栈/编程语言': '💻 编程/编程语言',
            '技术栈/Web开发': '💻 编程/Web开发',
            '技术栈/云服务 & DevOps': '💻 编程/DevOps运维',
            'Books': '📚 学习/书籍手册',
            '技术资料': '📚 学习/技术文档',
            'Lectures': '📚 学习/课程讲座',
            '社区': '👥 社区',
            '资讯': '📰 资讯',
            'Utils': '🛠️ 工具',
            '娱乐': '🎮 娱乐',
            '求职': '💼 求职',
            '未分类': '📂 其他',
            '新闻/资讯': '📰 资讯',
            '技术/编程': '💻 编程',
            '学习': '📚 学习',
            '生物信息': '🧬 生物',
            '人工智能': '🤖 AI',
            '编程开发': '💻 编程',
            '学习资料': '📚 学习',
            '技术社区': '👥 社区',
            '资讯媒体': '📰 资讯',
            '实用工具': '🛠️ 工具',
            '娱乐休闲': '🎮 娱乐',
            '稍后阅读': '📖 稍读',
            '求职招聘': '💼 求职',
            '其他分类': '📂 其他',
        }
        
        for bookmark in classified_bookmarks:
            category = bookmark['category']
            subcategory = bookmark.get('subcategory')
            
            # 标准化分类名称
            category = category_mapping.get(category, category)
            
            # 处理带斜杠的分类名称（如AI/模型与平台）
            if '/' in category:
                parts = category.split('/', 1)
                main_category = parts[0].strip()
                sub_category = parts[1].strip()
                
                # 创建主分类
                if main_category not in organized:
                    organized[main_category] = {'_items': [], '_subcategories': {}}
                
                # 创建子分类
                if sub_category not in organized[main_category]['_subcategories']:
                    organized[main_category]['_subcategories'][sub_category] = {'_items': []}
                
                organized[main_category]['_subcategories'][sub_category]['_items'].append(bookmark)
            else:
                # 处理传统的单层分类
                if category not in organized:
                    organized[category] = {'_items': [], '_subcategories': {}}
                
                if subcategory:
                    if subcategory not in organized[category]['_subcategories']:
                        organized[category]['_subcategories'][subcategory] = {'_items': []}
                    organized[category]['_subcategories'][subcategory]['_items'].append(bookmark)
                else:
                    organized[category]['_items'].append(bookmark)
        
        # 按置信度排序
        for category_data in organized.values():
            category_data['_items'].sort(key=lambda x: x['confidence'], reverse=True)
            
            for subcat_data in category_data['_subcategories'].values():
                subcat_data['_items'].sort(key=lambda x: x['confidence'], reverse=True)
        
        return organized
    
    def _export_results(self, organized_bookmarks: Dict, output_dir: str):
        """优化的导出处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 并行导出多种格式以节省时间
        export_tasks = [
            ('html', f"bookmarks_{timestamp}.html"),
            ('json', f"bookmarks_{timestamp}.json"),
            ('markdown', f"report_{timestamp}.md")
        ]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for format_type, filename in export_tasks:
                output_file = os.path.join(output_dir, filename)
                
                if format_type == 'html':
                    future = executor.submit(self.exporter.export_html, organized_bookmarks, output_file)
                elif format_type == 'json':
                    future = executor.submit(self.exporter.export_json, organized_bookmarks, output_file, self.stats)
                elif format_type == 'markdown':
                    future = executor.submit(self.exporter.export_markdown, organized_bookmarks, output_file, self.stats)
                
                futures.append(future)
            
            # 等待所有导出完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"导出失败: {e}")
        
        self.logger.info(f"结果已导出到: {output_dir}")
    
    def _train_models(self, classified_bookmarks: List[Dict]):
        """训练机器学习模型"""
        if not self.classifier.ml_classifier:
            self.logger.warning("机器学习组件未启用，跳过训练")
            return
        
        self.logger.info("开始训练机器学习模型...")
        
        # 准备训练数据
        training_data = []
        labels = []
        
        for bookmark in classified_bookmarks:
            if bookmark['confidence'] > 0.8:  # 只使用高置信度的数据训练
                features = self.classifier.extract_features(bookmark['url'], bookmark['title'])
                training_data.append(features)
                labels.append(bookmark['category'])
        
        if len(training_data) > 50:  # 需要足够的训练数据
            self.classifier.ml_classifier.train(training_data, labels)
            self.logger.info(f"模型训练完成，使用了 {len(training_data)} 个样本")
        else:
            self.logger.warning(f"训练数据不足 ({len(training_data)} 个样本)，跳过训练")
    
    def health_check(self, bookmarks: List[Dict]) -> Dict:
        """对书签进行健康检查"""
        self.logger.info(f"开始健康检查 {len(bookmarks)} 个书签...")
        
        results = self.health_checker.check_bookmarks(bookmarks)
        summary = self.health_checker.get_summary(results)
        
        self.logger.info(f"健康检查完成: {summary['accessible_count']}/{summary['total_count']} 个链接可访问")
        
        return summary
    
    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        classifier_stats = self.classifier.get_statistics()
        
        return {
            **self.stats,
            'classifier_stats': classifier_stats,
            'processing_speed': self.stats['processed_bookmarks'] / max(self.stats['processing_time'], 0.001),
            'success_rate': (self.stats['processed_bookmarks'] / max(self.stats['total_bookmarks'], 1)) * 100,
            'average_confidence': classifier_stats.get('average_confidence', 0.0)
        }