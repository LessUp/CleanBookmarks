"""
Bookmark Processor - 书签处理器

负责批量处理书签文件，协调各个组件完成整个分类流程
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

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
        self.max_workers = max_workers
        self.use_ml = use_ml
        
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.classifier = AIBookmarkClassifier(config_path, enable_ml=use_ml)
        self.deduplicator = BookmarkDeduplicator()
        self.health_checker = HealthChecker()
        self.exporter = DataExporter()
        
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
    
    def process_files(self, input_files: List[str], output_dir: str = "output", 
                     train_models: bool = False) -> Dict:
        """处理多个书签文件"""
        start_time = time.time()
        
        self.logger.info(f"开始处理 {len(input_files)} 个文件")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载所有书签
        all_bookmarks = []
        for file_path in input_files:
            bookmarks = self._load_bookmarks_from_file(file_path)
            all_bookmarks.extend(bookmarks)
            self.stats['files_processed'] += 1
        
        self.stats['total_bookmarks'] = len(all_bookmarks)
        
        if not all_bookmarks:
            self.logger.warning("没有找到有效的书签")
            return self.stats
        
        # 去重处理
        self.logger.info("开始去重处理...")
        unique_bookmarks, duplicates = self.deduplicator.remove_duplicates(all_bookmarks)
        self.stats['duplicates_removed'] = len(duplicates)
        
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
        """从HTML文件加载书签"""
        bookmarks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a')
            
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
        """并行分类书签"""
        classified_bookmarks = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交分类任务
            future_to_bookmark = {
                executor.submit(self._classify_single_bookmark, bookmark): bookmark
                for bookmark in bookmarks
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_bookmark):
                bookmark = future_to_bookmark[future]
                
                try:
                    result = future.result()
                    if result:
                        classified_bookmarks.append(result)
                    
                    completed += 1
                    if completed % 100 == 0:
                        progress = completed / len(bookmarks) * 100
                        self.logger.info(f"分类进度: {progress:.1f}% ({completed}/{len(bookmarks)})")
                        
                except Exception as e:
                    self.logger.error(f"分类失败 {bookmark.get('url', 'unknown')}: {e}")
                    self.stats['errors'] += 1
        
        return classified_bookmarks
    
    def _classify_single_bookmark(self, bookmark: Dict) -> Optional[Dict]:
        """分类单个书签"""
        try:
            url = bookmark['url']
            title = bookmark['title']
            
            # 使用AI分类器
            result = self.classifier.classify(url, title)
            
            # 构建结果
            classified_bookmark = {
                **bookmark,
                'category': result.category,
                'subcategory': result.subcategory,
                'confidence': result.confidence,
                'alternatives': result.alternatives,
                'reasoning': result.reasoning,
                'method': result.method,
                'processing_time': result.processing_time
            }
            
            # 更新分类统计
            category = result.category
            self.stats['categories_found'][category] = self.stats['categories_found'].get(category, 0) + 1
            
            return classified_bookmark
            
        except Exception as e:
            self.logger.error(f"单个书签分类失败: {e}")
            return None
    
    def _organize_bookmarks(self, classified_bookmarks: List[Dict]) -> Dict:
        """组织书签为层次结构"""
        organized = {}
        
        for bookmark in classified_bookmarks:
            category = bookmark['category']
            subcategory = bookmark.get('subcategory')
            
            # 创建分类结构
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
        """导出处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出HTML格式
        html_file = os.path.join(output_dir, f"bookmarks_{timestamp}.html")
        self.exporter.export_html(organized_bookmarks, html_file)
        
        # 导出JSON格式
        json_file = os.path.join(output_dir, f"bookmarks_{timestamp}.json")
        self.exporter.export_json(organized_bookmarks, json_file, self.stats)
        
        # 导出Markdown格式
        md_file = os.path.join(output_dir, f"report_{timestamp}.md")
        self.exporter.export_markdown(organized_bookmarks, md_file, self.stats)
        
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