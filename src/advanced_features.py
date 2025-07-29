"""
Advanced Features Module
高级功能模块

新增功能：
1. 智能书签去重
2. 个性化推荐系统
3. 批量导入导出
4. 书签健康检查
5. 统计分析
6. 书签同步
"""

import os
import sys
import json
import hashlib
import requests
import sqlite3
from typing import Dict, List, Tuple, Optional, Set, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse
from collections import defaultdict, Counter
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
from dataclasses import dataclass, field
import pickle

# 导入其他模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class BookmarkHealth:
    """书签健康状态"""
    url: str
    title: str
    status_code: int
    response_time: float
    is_accessible: bool
    error_message: str = ""
    last_checked: datetime = field(default_factory=datetime.now)
    redirect_url: str = ""

@dataclass
class SimilarityScore:
    """相似度评分"""
    bookmark1: Dict
    bookmark2: Dict
    similarity: float
    reasons: List[str]

class IntelligentDeduplicator:
    """智能书签去重器"""
    
    def __init__(self, similarity_threshold=0.85):
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
        
        # 预编译正则表达式
        self.url_patterns = {
            'youtube_video': re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)'),
            'github_repo': re.compile(r'github\.com/([\w-]+)/([\w-]+)'),
            'medium_article': re.compile(r'medium\.com/[^/]+/([\w-]+)'),
            'stackoverflow': re.compile(r'stackoverflow\.com/questions/(\d+)'),
        }
    
    def find_duplicates(self, bookmarks: List[Dict]) -> List[List[Dict]]:
        """查找重复书签组"""
        duplicate_groups = []
        processed = set()
        
        self.logger.info(f"开始查找重复书签，共 {len(bookmarks)} 个书签")
        
        for i, bookmark1 in enumerate(bookmarks):
            if i in processed:
                continue
            
            group = [bookmark1]
            processed.add(i)
            
            for j, bookmark2 in enumerate(bookmarks[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_similarity(bookmark1, bookmark2)
                if similarity.similarity >= self.similarity_threshold:
                    group.append(bookmark2)
                    processed.add(j)
            
            if len(group) > 1:
                duplicate_groups.append(group)
        
        self.logger.info(f"找到 {len(duplicate_groups)} 个重复组")
        return duplicate_groups
    
    def _calculate_similarity(self, bookmark1: Dict, bookmark2: Dict) -> SimilarityScore:
        """计算两个书签的相似度"""
        url1, title1 = bookmark1.get('url', ''), bookmark1.get('title', '')
        url2, title2 = bookmark2.get('url', ''), bookmark2.get('title', '')
        
        reasons = []
        scores = []
        
        # 1. URL相似度
        url_similarity = self._url_similarity(url1, url2)
        scores.append(url_similarity * 0.6)  # URL权重60%
        if url_similarity > 0.7:
            reasons.append(f"URL相似度: {url_similarity:.2f}")
        
        # 2. 标题相似度
        title_similarity = self._title_similarity(title1, title2)
        scores.append(title_similarity * 0.3)  # 标题权重30%
        if title_similarity > 0.7:
            reasons.append(f"标题相似度: {title_similarity:.2f}")
        
        # 3. 域名相似度
        domain_similarity = self._domain_similarity(url1, url2)
        scores.append(domain_similarity * 0.1)  # 域名权重10%
        if domain_similarity > 0.8:
            reasons.append(f"域名匹配: {domain_similarity:.2f}")
        
        final_similarity = sum(scores)
        
        return SimilarityScore(
            bookmark1=bookmark1,
            bookmark2=bookmark2,
            similarity=final_similarity,
            reasons=reasons
        )
    
    def _url_similarity(self, url1: str, url2: str) -> float:
        """计算URL相似度"""
        if not url1 or not url2:
            return 0.0
        
        # 完全相同
        if url1 == url2:
            return 1.0
        
        # 标准化URL
        normalized_url1 = self._normalize_url(url1)
        normalized_url2 = self._normalize_url(url2)
        
        if normalized_url1 == normalized_url2:
            return 0.95
        
        # 特定网站模式匹配
        for pattern_name, pattern in self.url_patterns.items():
            match1 = pattern.search(url1)
            match2 = pattern.search(url2)
            
            if match1 and match2:
                if match1.group(1) == match2.group(1):
                    return 0.9  # 同一资源的不同URL
        
        # 编辑距离相似度
        return self._string_similarity(normalized_url1, normalized_url2)
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        if not title1 or not title2:
            return 0.0
        
        # 标准化标题
        norm_title1 = self._normalize_title(title1)
        norm_title2 = self._normalize_title(title2)
        
        if norm_title1 == norm_title2:
            return 1.0
        
        # 词汇重叠度
        words1 = set(norm_title1.split())
        words2 = set(norm_title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        jaccard_similarity = intersection / union
        
        # 结合编辑距离
        edit_similarity = self._string_similarity(norm_title1, norm_title2)
        
        return max(jaccard_similarity, edit_similarity)
    
    def _domain_similarity(self, url1: str, url2: str) -> float:
        """计算域名相似度"""
        try:
            domain1 = urlparse(url1).netloc.lower().replace('www.', '')
            domain2 = urlparse(url2).netloc.lower().replace('www.', '')
            
            return 1.0 if domain1 == domain2 else 0.0
        except:
            return 0.0
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        try:
            parsed = urlparse(url.lower())
            
            # 移除常见跟踪参数
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'ref', 'source', 'from', 'campaign'
            ]
            
            if parsed.query:
                query_parts = []
                for part in parsed.query.split('&'):
                    if '=' in part:
                        key, value = part.split('=', 1)
                        if key not in tracking_params:
                            query_parts.append(part)
                query = '&'.join(query_parts)
            else:
                query = ''
            
            # 重构URL
            normalized = f"{parsed.scheme}://{parsed.netloc.replace('www.', '')}{parsed.path}"
            if query:
                normalized += f"?{query}"
            
            return normalized.rstrip('/')
            
        except:
            return url.lower()
    
    def _normalize_title(self, title: str) -> str:
        """标准化标题"""
        # 移除HTML实体
        import html
        title = html.unescape(title)
        
        # 移除特殊字符和多余空格
        title = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip().lower()
        
        return title
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度（使用Levenshtein距离）"""
        if s1 == s2:
            return 1.0
        
        if not s1 or not s2:
            return 0.0
        
        # 简化的编辑距离计算
        len1, len2 = len(s1), len(s2)
        
        if len1 > len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        
        # 如果长度差异太大，相似度很低
        if len2 > len1 * 2:
            return 0.0
        
        # 计算编辑距离
        current_row = list(range(len1 + 1))
        for i in range(1, len2 + 1):
            previous_row, current_row = current_row, [i] + [0] * len1
            for j in range(1, len1 + 1):
                add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
                if s1[j - 1] != s2[i - 1]:
                    change += 1
                current_row[j] = min(add, delete, change)
        
        edit_distance = current_row[len1]
        max_len = max(len1, len2)
        
        return 1.0 - (edit_distance / max_len)
    
    def suggest_best_bookmark(self, duplicate_group: List[Dict]) -> Dict:
        """从重复组中选择最佳书签"""
        if not duplicate_group:
            return None
        
        if len(duplicate_group) == 1:
            return duplicate_group[0]
        
        # 评分标准
        def score_bookmark(bookmark):
            score = 0
            url = bookmark.get('url', '')
            title = bookmark.get('title', '')
            
            # HTTPS加分
            if url.startswith('https://'):
                score += 2
            
            # 更短的URL加分（通常是canonical URL）
            if len(url) < 100:
                score += 1
            
            # 标题长度适中加分
            if 10 <= len(title) <= 100:
                score += 1
            
            # 没有跟踪参数加分
            if '?' not in url:
                score += 1
            
            # 知名域名加分
            domain = urlparse(url).netloc.lower()
            if any(trusted in domain for trusted in ['github.com', 'stackoverflow.com', 'wikipedia.org']):
                score += 2
            
            return score
        
        # 选择评分最高的书签
        best_bookmark = max(duplicate_group, key=score_bookmark)
        return best_bookmark
    
    def remove_duplicates(self, bookmarks: List[Dict], interactive=False) -> Tuple[List[Dict], List[Dict]]:
        """移除重复书签"""
        duplicate_groups = self.find_duplicates(bookmarks)
        
        if not duplicate_groups:
            return bookmarks, []
        
        removed_bookmarks = []
        unique_bookmarks = bookmarks.copy()
        
        for group in duplicate_groups:
            if interactive:
                best_bookmark = self._interactive_selection(group)
            else:
                best_bookmark = self.suggest_best_bookmark(group)
            
            # 移除组中的其他书签
            for bookmark in group:
                if bookmark != best_bookmark and bookmark in unique_bookmarks:
                    unique_bookmarks.remove(bookmark)
                    removed_bookmarks.append(bookmark)
        
        self.logger.info(f"移除了 {len(removed_bookmarks)} 个重复书签")
        return unique_bookmarks, removed_bookmarks
    
    def _interactive_selection(self, group: List[Dict]) -> Dict:
        """交互式选择最佳书签"""
        print(f"\n发现 {len(group)} 个相似书签:")
        for i, bookmark in enumerate(group):
            print(f"{i+1}. {bookmark.get('title', 'No title')}")
            print(f"   URL: {bookmark.get('url', 'No URL')}")
        
        suggested = self.suggest_best_bookmark(group)
        suggested_index = group.index(suggested) + 1
        
        while True:
            choice = input(f"请选择保留哪个 (1-{len(group)}, 回车选择推荐的 #{suggested_index}): ").strip()
            
            if not choice:
                return suggested
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(group):
                    return group[index]
                else:
                    print("无效选择，请重试")
            except ValueError:
                print("请输入数字")

class PersonalizedRecommendationSystem:
    """个性化推荐系统"""
    
    def __init__(self, model_path="models/recommendation.pkl"):
        self.model_path = model_path
        self.user_profile = defaultdict(float)
        self.category_preferences = defaultdict(float)
        self.domain_preferences = defaultdict(float)
        self.time_patterns = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        
        # 加载历史数据
        self._load_model()
    
    def learn_from_bookmarks(self, bookmarks: List[Dict]):
        """从现有书签学习用户偏好"""
        self.logger.info(f"从 {len(bookmarks)} 个书签学习用户偏好")
        
        for bookmark in bookmarks:
            category = bookmark.get('category', '未分类')
            domain = self._extract_domain(bookmark.get('url', ''))
            
            # 更新偏好权重
            self.category_preferences[category] += 1
            self.domain_preferences[domain] += 1
            
            # 记录时间模式（如果有时间戳）
            if 'timestamp' in bookmark:
                hour = bookmark['timestamp'].hour
                self.time_patterns[category].append(hour)
        
        # 归一化偏好分数
        self._normalize_preferences()
        
        # 保存模型
        self._save_model()
    
    def recommend_categories(self, url: str, title: str, n_recommendations: int = 3) -> List[Tuple[str, float]]:
        """推荐书签分类"""
        domain = self._extract_domain(url)
        current_hour = datetime.now().hour
        
        scores = defaultdict(float)
        
        # 基于域名偏好
        if domain in self.domain_preferences:
            for category in self.category_preferences:
                # 简化的关联计算
                scores[category] += self.domain_preferences[domain] * 0.3
        
        # 基于时间模式
        for category, hours in self.time_patterns.items():
            if hours:
                avg_hour = sum(hours) / len(hours)
                time_similarity = 1 - abs(current_hour - avg_hour) / 12
                scores[category] += time_similarity * self.category_preferences[category] * 0.2
        
        # 基于分类偏好
        for category, preference in self.category_preferences.items():
            scores[category] += preference * 0.5
        
        # 排序并返回推荐
        recommendations = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]
    
    def recommend_similar_bookmarks(self, target_bookmark: Dict, all_bookmarks: List[Dict], n_recommendations: int = 5) -> List[Dict]:
        """推荐相似书签"""
        target_category = target_bookmark.get('category', '')
        target_domain = self._extract_domain(target_bookmark.get('url', ''))
        target_title = target_bookmark.get('title', '').lower()
        
        scored_bookmarks = []
        
        for bookmark in all_bookmarks:
            if bookmark == target_bookmark:
                continue
            
            score = 0
            
            # 分类相似性
            if bookmark.get('category') == target_category:
                score += 3
            
            # 域名相似性
            if self._extract_domain(bookmark.get('url', '')) == target_domain:
                score += 2
            
            # 标题关键词相似性
            bookmark_title = bookmark.get('title', '').lower()
            common_words = set(target_title.split()) & set(bookmark_title.split())
            score += len(common_words) * 0.5
            
            if score > 0:
                scored_bookmarks.append((bookmark, score))
        
        # 排序并返回推荐
        scored_bookmarks.sort(key=lambda x: x[1], reverse=True)
        return [bookmark for bookmark, score in scored_bookmarks[:n_recommendations]]
    
    def get_trending_categories(self, days: int = 7) -> List[Tuple[str, int]]:
        """获取趋势分类"""
        # 这里简化处理，实际应该基于时间序列数据
        return sorted(self.category_preferences.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        try:
            return urlparse(url).netloc.lower().replace('www.', '')
        except:
            return ''
    
    def _normalize_preferences(self):
        """归一化偏好分数"""
        # 归一化分类偏好
        if self.category_preferences:
            total = sum(self.category_preferences.values())
            for category in self.category_preferences:
                self.category_preferences[category] /= total
        
        # 归一化域名偏好
        if self.domain_preferences:
            total = sum(self.domain_preferences.values())
            for domain in self.domain_preferences:
                self.domain_preferences[domain] /= total
    
    def _save_model(self):
        """保存推荐模型"""
        model_data = {
            'category_preferences': dict(self.category_preferences),
            'domain_preferences': dict(self.domain_preferences),
            'time_patterns': dict(self.time_patterns),
            'last_update': datetime.now().isoformat()
        }
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def _load_model(self):
        """加载推荐模型"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.category_preferences = defaultdict(float, model_data.get('category_preferences', {}))
                self.domain_preferences = defaultdict(float, model_data.get('domain_preferences', {}))
                self.time_patterns = defaultdict(list, model_data.get('time_patterns', {}))
                
                self.logger.info("推荐模型加载成功")
            except Exception as e:
                self.logger.error(f"推荐模型加载失败: {e}")

class BookmarkHealthChecker:
    """书签健康检查器"""
    
    def __init__(self, max_workers=10, timeout=10):
        self.max_workers = max_workers
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def check_bookmarks(self, bookmarks: List[Dict], progress_callback=None) -> List[BookmarkHealth]:
        """批量检查书签健康状态"""
        self.logger.info(f"开始检查 {len(bookmarks)} 个书签的健康状态")
        
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_bookmark = {
                executor.submit(self._check_single_bookmark, bookmark): bookmark
                for bookmark in bookmarks
            }
            
            # 处理结果
            for future in as_completed(future_to_bookmark):
                bookmark = future_to_bookmark[future]
                try:
                    health_status = future.result()
                    results.append(health_status)
                except Exception as e:
                    self.logger.error(f"检查书签失败 {bookmark.get('url')}: {e}")
                    results.append(BookmarkHealth(
                        url=bookmark.get('url', ''),
                        title=bookmark.get('title', ''),
                        status_code=0,
                        response_time=0.0,
                        is_accessible=False,
                        error_message=str(e)
                    ))
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(bookmarks))
        
        self.logger.info(f"健康检查完成，{len(results)} 个结果")
        return results
    
    def _check_single_bookmark(self, bookmark: Dict) -> BookmarkHealth:
        """检查单个书签"""
        url = bookmark.get('url', '')
        title = bookmark.get('title', '')
        
        if not url:
            return BookmarkHealth(
                url=url,
                title=title,
                status_code=0,
                response_time=0.0,
                is_accessible=False,
                error_message="空URL"
            )
        
        try:
            start_time = time.time()
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            response_time = time.time() - start_time
            
            return BookmarkHealth(
                url=url,
                title=title,
                status_code=response.status_code,
                response_time=response_time,
                is_accessible=response.status_code < 400,
                redirect_url=response.url if response.url != url else ""
            )
            
        except requests.exceptions.RequestException as e:
            return BookmarkHealth(
                url=url,
                title=title,
                status_code=0,
                response_time=0.0,
                is_accessible=False,
                error_message=str(e)
            )
    
    def get_health_summary(self, health_results: List[BookmarkHealth]) -> Dict:
        """获取健康检查摘要"""
        if not health_results:
            return {}
        
        accessible = sum(1 for h in health_results if h.is_accessible)
        inaccessible = len(health_results) - accessible
        
        avg_response_time = sum(h.response_time for h in health_results if h.is_accessible)
        avg_response_time = avg_response_time / accessible if accessible > 0 else 0
        
        status_codes = Counter(h.status_code for h in health_results)
        
        redirected = sum(1 for h in health_results if h.redirect_url)
        
        return {
            'total_checked': len(health_results),
            'accessible': accessible,
            'inaccessible': inaccessible,
            'accessibility_rate': accessible / len(health_results),
            'avg_response_time': avg_response_time,
            'redirected_count': redirected,
            'status_code_distribution': dict(status_codes),
            'slow_bookmarks': len([h for h in health_results if h.response_time > 5.0])
        }

class BatchImportExport:
    """批量导入导出工具"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def import_from_csv(self, csv_file: str) -> List[Dict]:
        """从CSV文件导入书签"""
        import csv
        
        bookmarks = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    bookmark = {
                        'url': row.get('url', ''),
                        'title': row.get('title', ''),
                        'category': row.get('category', '未分类'),
                        'tags': row.get('tags', '').split(',') if row.get('tags') else [],
                        'notes': row.get('notes', '')
                    }
                    bookmarks.append(bookmark)
            
            self.logger.info(f"从CSV导入了 {len(bookmarks)} 个书签")
            return bookmarks
            
        except Exception as e:
            self.logger.error(f"CSV导入失败: {e}")
            return []
    
    def export_to_csv(self, bookmarks: List[Dict], csv_file: str) -> bool:
        """导出书签到CSV文件"""
        import csv
        
        try:
            os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if not bookmarks:
                    return True
                
                fieldnames = ['url', 'title', 'category', 'tags', 'notes', 'confidence']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for bookmark in bookmarks:
                    row = {
                        'url': bookmark.get('url', ''),
                        'title': bookmark.get('title', ''),
                        'category': bookmark.get('category', ''),
                        'tags': ','.join(bookmark.get('tags', [])),
                        'notes': bookmark.get('notes', ''),
                        'confidence': bookmark.get('confidence', 0.0)
                    }
                    writer.writerow(row)
            
            self.logger.info(f"成功导出 {len(bookmarks)} 个书签到CSV")
            return True
            
        except Exception as e:
            self.logger.error(f"CSV导出失败: {e}")
            return False
    
    def import_from_json(self, json_file: str) -> List[Dict]:
        """从JSON文件导入书签"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                bookmarks = data
            elif isinstance(data, dict) and 'bookmarks' in data:
                bookmarks = data['bookmarks']
            else:
                raise ValueError("无效的JSON格式")
            
            self.logger.info(f"从JSON导入了 {len(bookmarks)} 个书签")
            return bookmarks
            
        except Exception as e:
            self.logger.error(f"JSON导入失败: {e}")
            return []
    
    def export_to_json(self, bookmarks: List[Dict], json_file: str) -> bool:
        """导出书签到JSON文件"""
        try:
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'total_bookmarks': len(bookmarks),
                    'format_version': '2.0'
                },
                'bookmarks': bookmarks
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"成功导出 {len(bookmarks)} 个书签到JSON")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON导出失败: {e}")
            return False