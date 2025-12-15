"""
Bookmark Processor - 书签处理器

负责批量处理书签文件，协调各个组件完成整个分类流程
"""

import json
import logging
import os
import time
import re
from .emoji_cleaner import clean_title as clean_emoji_title

from typing import List, Dict, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from bs4 import BeautifulSoup
from .ai_classifier import AIBookmarkClassifier
from .taxonomy_standardizer import TaxonomyStandardizer

try:
    from .llm_organizer import LLMBookmarkOrganizer
except ImportError:
    LLMBookmarkOrganizer = None

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

        # 标准化层（受控词表）
        self.standardizer = TaxonomyStandardizer(self.config)

        # 延迟初始化组件以避免启动开销
        self._classifier = None
        self._deduplicator = None
        self._health_checker = None
        self._exporter = None
        self._llm_organizer = None
        self.llm_organizer_meta: Optional[Dict] = None
        
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
            'files_processed': 0,
            'llm_organizer_used': False,
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
    
    @property
    def llm_organizer(self) -> Optional[LLMBookmarkOrganizer]:
        """Lazy loading LLM organizer"""
        if self._llm_organizer is None and LLMBookmarkOrganizer is not None:
            try:
                self._llm_organizer = LLMBookmarkOrganizer(
                    config_path=self.config_path,
                    config=self.config
                )
            except Exception as exc:
                self.logger.warning(f"LLM organizer init failed: {exc}")
                self._llm_organizer = None
        return self._llm_organizer
    
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
        
        # 对剩余书签执行高级去重（始终执行，提升跨浏览器合并的去重质量）
        unique_bookmarks, duplicates = self.deduplicator.remove_duplicates(fast_unique)
        self.stats['duplicates_removed'] = fast_duplicates_removed + len(duplicates)
        
        # 并行分类处理
        self.logger.info(f"开始分类 {len(unique_bookmarks)} 个书签...")
        classified_bookmarks = self._classify_bookmarks_parallel(unique_bookmarks)
        
        # 组织分类结果
        organized_bookmarks = self._organize_bookmarks(classified_bookmarks)

        # 可选：调用 LLM 进行更高层次的整理
        self.llm_organizer_meta = None
        if self.llm_organizer and self.llm_organizer.enabled():
            try:
                llm_result = self.llm_organizer.organize(
                    bookmarks=classified_bookmarks,
                    baseline=organized_bookmarks
                )
            except Exception as exc:
                self.logger.warning(f"LLM organizer execution failed: {exc}")
                llm_result = None

            if llm_result and llm_result.get('organized'):
                organized_bookmarks = llm_result['organized']
                self.llm_organizer_meta = llm_result.get('meta')
                self.stats['llm_organizer_used'] = True
                if self.llm_organizer_meta:
                    self.stats['llm_organizer_meta'] = self.llm_organizer_meta
                elif 'llm_organizer_meta' in self.stats:
                    self.stats.pop('llm_organizer_meta', None)
            else:
                self.stats['llm_organizer_used'] = False
                if 'llm_organizer_meta' in self.stats:
                    self.stats.pop('llm_organizer_meta', None)
        else:
            self.stats['llm_organizer_used'] = False
            if 'llm_organizer_meta' in self.stats:
                self.stats.pop('llm_organizer_meta', None)

        organized_bookmarks = self._sort_organized_structure(organized_bookmarks)
        
        # 更新统计
        self.stats['processing_time'] = time.time() - start_time
        self.stats['processed_bookmarks'] = len(classified_bookmarks)
        
        # 导出结果
        self._export_results(organized_bookmarks, output_dir)
        
        # 训练模型（如果启用）
        if train_models and self.use_ml:
            self._train_models(classified_bookmarks)
        
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
                title_raw = (link.string or link.get_text() or '').strip()
                # 统一使用预处理模块清理标题前缀emoji，防止多次导出叠加
                title = clean_emoji_title(title_raw)

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
                    'processing_time': result.processing_time if hasattr(result, 'processing_time') else 0.0,
                    'facets': result.facets if hasattr(result, 'facets') else {}
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
                    'processing_time': result.get('processing_time', 0.0),
                    'facets': result.get('facets', {})
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
        """按 subject -> resource_type 两级组织（受控词表标准化）。"""
        organized: Dict[str, Dict] = {}

        for bookmark in classified_bookmarks:
            category = (bookmark.get('category') or '').strip()
            subcategory = (bookmark.get('subcategory') or '').strip() or None

            # 从分类派生 subject / resource_type
            derived_subject, derived_rt = self.standardizer.derive_from_category(
                category, content_type=None
            )

            # 标准化 subject 与 resource_type
            subject = derived_subject or self.standardizer.normalize_subject(category) or '其他'
            # 优先使用规则引擎提供的 resource_type 分面提示
            facets = bookmark.get('facets') or {}
            facet_rt_hint = facets.get('resource_type_hint') if isinstance(facets, dict) else None
            facet_rt_std = self.standardizer.normalize_resource_type(facet_rt_hint) if facet_rt_hint else None
            resource_type = facet_rt_std or self.standardizer.normalize_resource_type(subcategory) or derived_rt

            # 初始化 subject 节点
            if subject not in organized:
                organized[subject] = {'_items': [], '_subcategories': {}}

            # 放入 resource_type 子类或直接归于 subject
            if resource_type:
                if resource_type not in organized[subject]['_subcategories']:
                    organized[subject]['_subcategories'][resource_type] = {'_items': []}
                organized[subject]['_subcategories'][resource_type]['_items'].append(bookmark)
            else:
                organized[subject]['_items'].append(bookmark)

        return self._sort_organized_structure(organized)

    def _sort_organized_structure(self, organized: Optional[Dict]) -> Dict:
        """统一的排序逻辑，保证导出结果有序。"""
        if not organized:
            return {}

        for subject_data in organized.values():
            items = subject_data.get('_items', [])
            items.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
            subject_data['_items'] = items

            subcategories = subject_data.get('_subcategories', {})
            for sub_data in subcategories.values():
                sub_items = sub_data.get('_items', [])
                sub_items.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
                sub_data['_items'] = sub_items
            subject_data['_subcategories'] = subcategories

        return organized
    
    def _export_results(self, organized_bookmarks: Dict, output_dir: str):
        """优化的导出处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 在导出前获取最终的统计数据
        final_stats = self.get_statistics()

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
                    future = executor.submit(self.exporter.export_html, organized_bookmarks, output_file, final_stats)
                elif format_type == 'json':
                    future = executor.submit(self.exporter.export_json, organized_bookmarks, output_file, final_stats)
                elif format_type == 'markdown':
                    future = executor.submit(self.exporter.export_markdown, organized_bookmarks, output_file, final_stats)
                
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
        samples_added = 0
        for bookmark in classified_bookmarks:
            if bookmark.get('confidence', 0.0) > 0.8:  # 只使用高置信度的数据训练
                features = self.classifier.extract_features(bookmark['url'], bookmark['title'])
                self.classifier.ml_classifier.add_training_sample(features, bookmark['category'])
                samples_added += 1
        
        if samples_added > 50:  # 需要足够的训练数据
            self.logger.info(f"使用 {samples_added} 个样本进行训练...")
            if self.classifier.ml_classifier.train_model():
                self.logger.info(f"模型训练完成。")
            else:
                self.logger.error("模型训练失败。")
        else:
            self.logger.warning(f"训练数据不足 ({samples_added} 个样本)，跳过训练")
    
    def health_check(self, bookmarks: List[Dict]) -> Dict:
        """对书签进行健康检查"""
        self.logger.info(f"开始健康检查 {len(bookmarks)} 个书签...")
        
        results = self.health_checker.check_bookmarks(bookmarks)
        summary = self.health_checker.get_summary(results)
        
        self.logger.info(f"健康检查完成: {summary['accessible_count']}/{summary['total_count']} 个链接可访问")
        
        return summary
    
    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        # 确保分类器已经被初始化
        if self._classifier:
            classifier_stats = self.classifier.get_statistics()
        else:
            classifier_stats = {}

        # 计算处理速度和成功率
        processing_time = self.stats.get('processing_time', 0.0)
        processed_bookmarks = self.stats.get('processed_bookmarks', 0)
        total_bookmarks = self.stats.get('total_bookmarks', 1)

        llm_stats = None
        if self.llm_organizer:
            llm_stats = self.llm_organizer.get_stats()

        return {
            **self.stats,
            'classifier_stats': classifier_stats,
            'processing_speed_bps': processed_bookmarks / max(processing_time, 0.001), # bookmarks per second
            'success_rate_percent': (processed_bookmarks / max(total_bookmarks, 1)) * 100,
            'llm_organizer_stats': llm_stats,
        }
