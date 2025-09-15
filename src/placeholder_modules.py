"""
占位符模块 - 待完整实现

这些模块包含基础框架，需要进一步完善实现
"""

# semantic_analyzer.py
import re
import math
from collections import Counter
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

class SemanticAnalyzer:
    """语义分析器 - 基于词向量和语义相似度的分类"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.category_keywords = self._load_category_keywords()
        self.stopwords = self._load_stopwords()
        self.word_vectors = {}  # 简化的词向量存储
        self._initialize_semantic_rules()
    
    def _load_category_keywords(self) -> Dict[str, List[str]]:
        """加载分类关键词库"""
        return {
            "AI/机器学习": [
                "artificial", "intelligence", "machine", "learning", "neural", "network", 
                "deep", "tensorflow", "pytorch", "algorithm", "model", "training",
                "人工智能", "机器学习", "深度学习", "神经网络", "模型", "算法"
            ],
            "技术/编程": [
                "programming", "coding", "development", "software", "code", "developer",
                "python", "javascript", "java", "github", "api", "framework",
                "编程", "开发", "代码", "软件", "技术", "程序"
            ],
            "学习/教育": [
                "tutorial", "course", "education", "learning", "study", "guide",
                "documentation", "reference", "manual", "book", "article",
                "教程", "课程", "学习", "教育", "文档", "指南", "手册"
            ],
            "资讯": [
                "news", "article", "blog", "post", "update", "information",
                "media", "press", "report", "story", "breaking",
                "新闻", "资讯", "博客", "文章", "报道", "媒体"
            ],
            "工具/软件": [
                "tool", "software", "application", "utility", "program", "service",
                "platform", "system", "interface", "dashboard", "app",
                "工具", "软件", "应用", "平台", "系统", "服务"
            ]
        }
    
    def _load_stopwords(self) -> Set[str]:
        """加载停用词列表"""
        return {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "this", "that", "these", "those", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may", "might",
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
            "一", "也", "上", "他", "她", "它", "们", "来", "去", "说", "要"
        }
    
    def _initialize_semantic_rules(self):
        """初始化语义规则"""
        self.domain_patterns = {
            r'github\.com': '技术/编程',
            r'stackoverflow\.com': '技术/编程',
            r'medium\.com': '学习/教育',
            r'youtube\.com': '娱乐/视频', 
            r'news\.|bbc\.|cnn\.|reuters\.': '新闻/资讯',
            r'wikipedia\.org': '学习/教育',
            r'docs\.|documentation': '学习/教育'
        }
    
    def classify(self, features) -> Optional[Dict]:
        """基于语义分析的分类"""
        try:
            url = features.url
            title = features.title
            domain = features.domain
            
            # 1. 域名语义分析
            domain_score = self._analyze_domain_semantics(domain)
            
            # 2. 标题语义分析
            title_score = self._analyze_title_semantics(title)
            
            # 3. URL路径语义分析
            path_score = self._analyze_path_semantics(url)
            
            # 4. 综合语义评分
            combined_scores = self._combine_semantic_scores(
                domain_score, title_score, path_score
            )
            
            if not combined_scores:
                return None
            
            # 选择最高分的分类
            best_category = max(combined_scores, key=combined_scores.get)
            confidence = combined_scores[best_category]
            
            if confidence < 0.3:  # 置信度阈值
                return None
            
            return {
                'category': best_category,
                'confidence': confidence,
                'reasoning': [f'语义分析: {best_category} (置信度: {confidence:.2f})'],
                'method': 'semantic_analyzer',
                'semantic_scores': combined_scores
            }
            
        except Exception as e:
            return None
    
    def _analyze_domain_semantics(self, domain: str) -> Dict[str, float]:
        """分析域名语义"""
        scores = {}
        
        # 检查域名模式
        for pattern, category in self.domain_patterns.items():
            if re.search(pattern, domain, re.IGNORECASE):
                scores[category] = scores.get(category, 0) + 0.8
        
        # 检查域名中的关键词
        domain_words = re.findall(r'[a-zA-Z]+', domain.lower())
        for word in domain_words:
            if len(word) > 2 and word not in self.stopwords:
                for category, keywords in self.category_keywords.items():
                    if word in [kw.lower() for kw in keywords]:
                        scores[category] = scores.get(category, 0) + 0.3
        
        return scores
    
    def _analyze_title_semantics(self, title: str) -> Dict[str, float]:
        """分析标题语义"""
        scores = {}
        
        if not title:
            return scores
        
        # 提取关键词
        title_words = self._extract_keywords(title)
        
        # 计算TF-IDF相似度
        for category, keywords in self.category_keywords.items():
            similarity = self._calculate_similarity(title_words, keywords)
            if similarity > 0:
                scores[category] = similarity
        
        return scores
    
    def _analyze_path_semantics(self, url: str) -> Dict[str, float]:
        """分析URL路径语义"""
        scores = {}
        
        try:
            parsed = urlparse(url)
            path_words = re.findall(r'[a-zA-Z]+', parsed.path.lower())
            
            for word in path_words:
                if len(word) > 2 and word not in self.stopwords:
                    for category, keywords in self.category_keywords.items():
                        if word in [kw.lower() for kw in keywords]:
                            scores[category] = scores.get(category, 0) + 0.2
        
        except Exception:
            pass
        
        return scores
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        words = re.findall(r'[a-zA-Z\u4e00-\u9fff]+', text.lower())
        keywords = []
        
        for word in words:
            if len(word) > 2 and word not in self.stopwords:
                keywords.append(word)
        
        return keywords
    
    def _calculate_similarity(self, text_words: List[str], category_keywords: List[str]) -> float:
        """计算文本与分类关键词的相似度"""
        if not text_words or not category_keywords:
            return 0.0
        
        # 转换为小写进行比较
        text_words_lower = [w.lower() for w in text_words]
        category_keywords_lower = [w.lower() for w in category_keywords]
        
        # 计算交集
        intersection = set(text_words_lower) & set(category_keywords_lower)
        
        if not intersection:
            return 0.0
        
        # 计算Jaccard相似度
        union = set(text_words_lower) | set(category_keywords_lower)
        jaccard = len(intersection) / len(union)
        
        # 增加权重，考虑匹配词的重要性
        importance_weight = len(intersection) / max(len(text_words_lower), 1)
        
        return min(jaccard * 2 + importance_weight * 0.5, 1.0)
    
    def _combine_semantic_scores(self, domain_scores: Dict, title_scores: Dict, path_scores: Dict) -> Dict[str, float]:
        """综合语义评分"""
        combined = {}
        all_categories = set(domain_scores.keys()) | set(title_scores.keys()) | set(path_scores.keys())
        
        for category in all_categories:
            domain_score = domain_scores.get(category, 0) * 0.4  # 域名权重40%
            title_score = title_scores.get(category, 0) * 0.5   # 标题权重50% 
            path_score = path_scores.get(category, 0) * 0.1     # 路径权重10%
            
            combined[category] = domain_score + title_score + path_score
        
        # 归一化
        if combined:
            max_score = max(combined.values())
            if max_score > 0:
                combined = {k: v / max_score for k, v in combined.items()}
        
        return combined

# user_profiler.py  
import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

class UserProfiler:
    """用户画像分析器 - 基于用户行为的个性化分类"""
    
    def __init__(self, profile_file: str = 'user_profile.json'):
        self.profile_file = profile_file
        self.preferences = self._load_preferences()
        self.learning_rate = 0.1
        self.decay_factor = 0.95  # 时间衰减因子
        self._initialize_profile_structure()
    
    def _load_preferences(self) -> Dict:
        """加载用户偏好数据"""
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return self._create_default_profile()
    
    def _create_default_profile(self) -> Dict:
        """创建默认用户画像"""
        return {
            'category_preferences': {},  # 分类偏好
            'domain_preferences': {},    # 域名偏好
            'keyword_preferences': {},   # 关键词偏好
            'time_patterns': {},         # 时间模式
            'interaction_history': [],   # 交互历史
            'confidence_adjustments': {},# 置信度调整
            'last_updated': datetime.now().isoformat(),
            'profile_version': '1.0'
        }
    
    def _initialize_profile_structure(self):
        """初始化画像结构"""
        required_keys = [
            'category_preferences', 'domain_preferences', 'keyword_preferences',
            'time_patterns', 'interaction_history', 'confidence_adjustments'
        ]
        
        for key in required_keys:
            if key not in self.preferences:
                self.preferences[key] = {} if key != 'interaction_history' else []
    
    def classify(self, features) -> Optional[Dict]:
        """基于用户画像的分类"""
        try:
            url = features.url
            title = features.title
            domain = features.domain
            
            # 1. 基于历史偏好计算分类得分
            category_scores = self._calculate_category_scores(features)
            
            # 2. 基于域名偏好调整
            domain_adjustments = self._get_domain_adjustments(domain)
            
            # 3. 基于关键词偏好调整
            keyword_adjustments = self._get_keyword_adjustments(title)
            
            # 4. 基于时间模式调整
            time_adjustments = self._get_time_adjustments()
            
            # 5. 综合计算最终得分
            final_scores = self._combine_scores(
                category_scores, domain_adjustments, 
                keyword_adjustments, time_adjustments
            )
            
            if not final_scores:
                return None
            
            # 选择最佳分类
            best_category = max(final_scores, key=final_scores.get)
            confidence = final_scores[best_category]
            
            # 应用置信度调整
            confidence = self._apply_confidence_adjustments(best_category, confidence)
            
            if confidence < 0.2:  # 用户画像的阈值较低
                return None
            
            return {
                'category': best_category,
                'confidence': confidence,
                'reasoning': [f'用户画像分析: {best_category} (个性化置信度: {confidence:.2f})'],
                'method': 'user_profiler',
                'profile_scores': final_scores
            }
            
        except Exception as e:
            return None
    
    def _calculate_category_scores(self, features) -> Dict[str, float]:
        """计算分类基础得分"""
        scores = {}
        category_prefs = self.preferences.get('category_preferences', {})
        
        # 基于历史分类频率
        total_interactions = sum(category_prefs.values())
        if total_interactions > 0:
            for category, count in category_prefs.items():
                scores[category] = count / total_interactions
        
        return scores
    
    def _get_domain_adjustments(self, domain: str) -> Dict[str, float]:
        """获取域名偏好调整"""
        adjustments = {}
        domain_prefs = self.preferences.get('domain_preferences', {})
        
        if domain in domain_prefs:
            # 基于域名历史分类的加权
            domain_data = domain_prefs[domain]
            total_visits = sum(domain_data.values()) if isinstance(domain_data, dict) else 0
            
            if total_visits > 0:
                for category, count in domain_data.items():
                    if isinstance(count, (int, float)):
                        adjustments[category] = (count / total_visits) * 0.3
        
        return adjustments
    
    def _get_keyword_adjustments(self, title: str) -> Dict[str, float]:
        """获取关键词偏好调整"""
        adjustments = {}
        keyword_prefs = self.preferences.get('keyword_preferences', {})
        
        if not title:
            return adjustments
        
        # 提取标题中的关键词
        title_words = self._extract_words(title)
        
        for word in title_words:
            if word in keyword_prefs:
                keyword_data = keyword_prefs[word]
                if isinstance(keyword_data, dict):
                    total_occurrences = sum(keyword_data.values())
                    if total_occurrences > 0:
                        for category, count in keyword_data.items():
                            if isinstance(count, (int, float)):
                                weight = (count / total_occurrences) * 0.2
                                adjustments[category] = adjustments.get(category, 0) + weight
        
        return adjustments
    
    def _get_time_adjustments(self) -> Dict[str, float]:
        """获取时间模式调整"""
        adjustments = {}
        time_patterns = self.preferences.get('time_patterns', {})
        
        current_hour = datetime.now().hour
        time_slot = self._get_time_slot(current_hour)
        
        if time_slot in time_patterns:
            slot_data = time_patterns[time_slot]
            if isinstance(slot_data, dict):
                total_activities = sum(slot_data.values())
                if total_activities > 0:
                    for category, count in slot_data.items():
                        if isinstance(count, (int, float)):
                            adjustments[category] = (count / total_activities) * 0.1
        
        return adjustments
    
    def _get_time_slot(self, hour: int) -> str:
        """获取时间段"""
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 24:
            return 'evening'
        else:
            return 'night'
    
    def _combine_scores(self, base_scores: Dict, domain_adj: Dict, 
                       keyword_adj: Dict, time_adj: Dict) -> Dict[str, float]:
        """综合所有得分"""
        combined = defaultdict(float)
        
        # 合并所有得分
        for category, score in base_scores.items():
            combined[category] += score
        
        for category, adjustment in domain_adj.items():
            combined[category] += adjustment
        
        for category, adjustment in keyword_adj.items():
            combined[category] += adjustment
        
        for category, adjustment in time_adj.items():
            combined[category] += adjustment
        
        return dict(combined)
    
    def _apply_confidence_adjustments(self, category: str, confidence: float) -> float:
        """应用置信度调整"""
        adjustments = self.preferences.get('confidence_adjustments', {})
        
        if category in adjustments:
            adjustment_factor = adjustments[category]
            confidence *= (1 + adjustment_factor)
        
        return min(max(confidence, 0.0), 1.0)
    
    def _extract_words(self, text: str) -> List[str]:
        """提取文本中的单词"""
        import re
        words = re.findall(r'[a-zA-Z\u4e00-\u9fff]{2,}', text.lower())
        return [w for w in words if len(w) > 2]
    
    def update_preferences(self, features, category: str, confidence: float = 1.0):
        """更新用户偏好"""
        try:
            url = features.url
            title = features.title  
            domain = features.domain
            
            # 1. 更新分类偏好
            category_prefs = self.preferences['category_preferences']
            category_prefs[category] = category_prefs.get(category, 0) + confidence
            
            # 2. 更新域名偏好
            domain_prefs = self.preferences['domain_preferences']
            if domain not in domain_prefs:
                domain_prefs[domain] = {}
            domain_prefs[domain][category] = domain_prefs[domain].get(category, 0) + confidence
            
            # 3. 更新关键词偏好
            if title:
                words = self._extract_words(title)
                keyword_prefs = self.preferences['keyword_preferences']
                
                for word in words[:5]:  # 只取前5个关键词
                    if word not in keyword_prefs:
                        keyword_prefs[word] = {}
                    keyword_prefs[word][category] = keyword_prefs[word].get(category, 0) + confidence * 0.5
            
            # 4. 更新时间模式
            current_hour = datetime.now().hour
            time_slot = self._get_time_slot(current_hour)
            time_patterns = self.preferences['time_patterns']
            
            if time_slot not in time_patterns:
                time_patterns[time_slot] = {}
            time_patterns[time_slot][category] = time_patterns[time_slot].get(category, 0) + confidence * 0.3
            
            # 5. 记录交互历史
            interaction = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'title': title,
                'domain': domain,
                'category': category,
                'confidence': confidence
            }
            
            history = self.preferences['interaction_history']
            history.append(interaction)
            
            # 保持历史记录在合理范围内（最多1000条）
            if len(history) > 1000:
                self.preferences['interaction_history'] = history[-1000:]
            
            # 6. 更新时间戳
            self.preferences['last_updated'] = datetime.now().isoformat()
            
            # 7. 应用时间衰减
            self._apply_time_decay()
            
            # 8. 保存更新
            self._save_preferences()
            
        except Exception as e:
            pass  # 静默失败，不影响主流程
    
    def _apply_time_decay(self):
        """应用时间衰减因子"""
        try:
            last_updated = datetime.fromisoformat(self.preferences.get('last_updated', datetime.now().isoformat()))
            days_elapsed = (datetime.now() - last_updated).days
            
            if days_elapsed > 0:
                decay_rate = self.decay_factor ** days_elapsed
                
                # 对数值型偏好应用衰减
                for pref_type in ['category_preferences', 'domain_preferences', 'keyword_preferences', 'time_patterns']:
                    prefs = self.preferences.get(pref_type, {})
                    self._apply_decay_to_nested_dict(prefs, decay_rate)
        
        except Exception:
            pass
    
    def _apply_decay_to_nested_dict(self, data: Dict, decay_rate: float):
        """对嵌套字典应用衰减"""
        for key, value in data.items():
            if isinstance(value, dict):
                self._apply_decay_to_nested_dict(value, decay_rate)
            elif isinstance(value, (int, float)):
                data[key] = value * decay_rate
    
    def _save_preferences(self):
        """保存用户偏好"""
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def export_profile(self) -> Dict:
        """导出用户画像"""
        return self.preferences.copy()
    
    def import_profile(self, profile: Dict):
        """导入用户画像"""
        if isinstance(profile, dict):
            self.preferences = profile
            self._initialize_profile_structure()
            self._save_preferences()
    
    def get_user_insights(self) -> Dict:
        """获取用户行为洞察"""
        insights = {
            'total_interactions': len(self.preferences.get('interaction_history', [])),
            'favorite_categories': {},
            'favorite_domains': {},
            'activity_patterns': {},
            'last_active': self.preferences.get('last_updated', '')
        }
        
        # 分析最喜欢的分类
        category_prefs = self.preferences.get('category_preferences', {})
        if category_prefs:
            total = sum(category_prefs.values())
            insights['favorite_categories'] = {
                k: round(v/total * 100, 1) for k, v in 
                sorted(category_prefs.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        # 分析最常访问的域名
        domain_prefs = self.preferences.get('domain_preferences', {})
        domain_totals = {}
        for domain, categories in domain_prefs.items():
            if isinstance(categories, dict):
                domain_totals[domain] = sum(categories.values())
        
        if domain_totals:
            insights['favorite_domains'] = dict(sorted(domain_totals.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # 分析活动模式
        time_patterns = self.preferences.get('time_patterns', {})
        if time_patterns:
            for time_slot, activities in time_patterns.items():
                if isinstance(activities, dict):
                    insights['activity_patterns'][time_slot] = sum(activities.values())
        
        return insights

# performance_monitor.py
class PerformanceMonitor:
    """性能监控器 - 待完整实现"""
    
    def __init__(self):
        self.metrics = {}
    
    def get_summary(self):
        """获取性能摘要"""
        return self.metrics

# deduplicator.py
import re
import hashlib
from urllib.parse import urlparse, parse_qs, urljoin
from typing import List, Dict, Tuple, Set
from difflib import SequenceMatcher
from collections import defaultdict

class BookmarkDeduplicator:
    """书签去重器 - 高级相似度检测和去重"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.title_threshold = 0.8
        self.url_threshold = 0.9
        
        # 初始化去重策略
        self.dedup_strategies = [
            self._exact_url_match,
            self._normalized_url_match,
            self._content_similarity_match,
            self._title_similarity_match,
            self._domain_path_similarity
        ]
    
    def remove_duplicates(self, bookmarks: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """移除重复书签 - 高级算法"""
        if not bookmarks:
            return [], []
        
        unique_bookmarks = []
        duplicates = []
        processed_indices = set()
        
        # 为每个书签生成唯一标识
        for i, bookmark in enumerate(bookmarks):
            bookmark['_original_index'] = i
        
        # 逐一比较书签
        for i, bookmark1 in enumerate(bookmarks):
            if i in processed_indices:
                continue
            
            # 找到所有与当前书签相似的书签
            similar_group = [bookmark1]
            similar_indices = {i}
            
            for j, bookmark2 in enumerate(bookmarks[i+1:], i+1):
                if j in processed_indices:
                    continue
                
                if self._are_duplicates(bookmark1, bookmark2):
                    similar_group.append(bookmark2)
                    similar_indices.add(j)
            
            # 处理相似组
            if len(similar_group) > 1:
                # 选择最佳代表
                best_bookmark = self._select_best_bookmark(similar_group)
                unique_bookmarks.append(best_bookmark)
                
                # 其余的标记为重复
                for bookmark in similar_group:
                    if bookmark != best_bookmark:
                        bookmark['duplicate_reason'] = self._get_duplicate_reason(best_bookmark, bookmark)
                        duplicates.append(bookmark)
            else:
                # 没有重复，直接添加
                unique_bookmarks.append(bookmark1)
            
            # 标记为已处理
            processed_indices.update(similar_indices)
        
        return unique_bookmarks, duplicates
    
    def _are_duplicates(self, bookmark1: Dict, bookmark2: Dict) -> bool:
        """判断两个书签是否重复"""
        # 尝试所有去重策略
        for strategy in self.dedup_strategies:
            if strategy(bookmark1, bookmark2):
                return True
        return False
    
    def _exact_url_match(self, bookmark1: Dict, bookmark2: Dict) -> bool:
        """精确URL匹配"""
        return bookmark1.get('url', '') == bookmark2.get('url', '')
    
    def _normalized_url_match(self, bookmark1: Dict, bookmark2: Dict) -> bool:
        """标准化URL匹配"""
        url1_norm = self._normalize_url(bookmark1.get('url', ''))
        url2_norm = self._normalize_url(bookmark2.get('url', ''))
        
        if not url1_norm or not url2_norm:
            return False
        
        # 计算URL相似度
        similarity = self._calculate_url_similarity(url1_norm, url2_norm)
        return similarity >= self.url_threshold
    
    def _content_similarity_match(self, bookmark1: Dict, bookmark2: Dict) -> bool:
        """内容相似度匹配"""
        # 综合考虑标题和URL的相似度
        title_sim = self._calculate_title_similarity(
            bookmark1.get('title', ''), bookmark2.get('title', '')
        )
        
        url_sim = self._calculate_url_similarity(
            bookmark1.get('url', ''), bookmark2.get('url', '')
        )
        
        # 加权平均
        combined_similarity = (title_sim * 0.6 + url_sim * 0.4)
        return combined_similarity >= self.similarity_threshold
    
    def _title_similarity_match(self, bookmark1: Dict, bookmark2: Dict) -> bool:
        """标题相似度匹配"""
        title1 = bookmark1.get('title', '').strip()
        title2 = bookmark2.get('title', '').strip()
        
        if not title1 or not title2:
            return False
        
        similarity = self._calculate_title_similarity(title1, title2)
        return similarity >= self.title_threshold
    
    def _domain_path_similarity(self, bookmark1: Dict, bookmark2: Dict) -> bool:
        """域名和路径相似度匹配"""
        try:
            parsed1 = urlparse(bookmark1.get('url', ''))
            parsed2 = urlparse(bookmark2.get('url', ''))
            
            # 域名必须相同
            if parsed1.netloc != parsed2.netloc:
                return False
            
            # 计算路径相似度
            path_sim = SequenceMatcher(None, parsed1.path, parsed2.path).ratio()
            
            # 如果路径非常相似，认为是重复
            return path_sim >= 0.9
            
        except Exception:
            return False
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        if not url:
            return ''
        
        try:
            parsed = urlparse(url.lower().strip())
            
            # 移除常见的跟踪参数
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
                'fbclid', 'gclid', 'msclkid', '_ga', 'ref', 'source'
            }
            
            # 过滤查询参数
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items() 
                if k not in tracking_params
            }
            
            # 重建查询字符串
            query_string = '&'.join([f"{k}={'&'.join(v)}" for k, v in sorted(filtered_params.items())])
            
            # 标准化路径（移除末尾斜杠）
            path = parsed.path.rstrip('/')
            
            # 重构URL
            normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
            if query_string:
                normalized += f"?{query_string}"
            
            return normalized
            
        except Exception:
            return url.lower().strip()
    
    def _calculate_url_similarity(self, url1: str, url2: str) -> float:
        """计算URL相似度"""
        if not url1 or not url2:
            return 0.0
        
        try:
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)
            
            # 域名相似度
            domain_sim = 1.0 if parsed1.netloc == parsed2.netloc else 0.0
            
            # 路径相似度
            path_sim = SequenceMatcher(None, parsed1.path, parsed2.path).ratio()
            
            # 查询参数相似度
            query_sim = SequenceMatcher(None, parsed1.query, parsed2.query).ratio()
            
            # 加权平均
            overall_sim = domain_sim * 0.5 + path_sim * 0.3 + query_sim * 0.2
            
            return overall_sim
            
        except Exception:
            # 如果解析失败，使用字符串相似度
            return SequenceMatcher(None, url1, url2).ratio()
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        if not title1 or not title2:
            return 0.0
        
        # 清理标题
        clean_title1 = self._clean_title(title1)
        clean_title2 = self._clean_title(title2)
        
        if not clean_title1 or not clean_title2:
            return 0.0
        
        # 计算多种相似度
        sequence_sim = SequenceMatcher(None, clean_title1, clean_title2).ratio()
        
        # 词级别相似度
        words1 = set(clean_title1.split())
        words2 = set(clean_title2.split())
        
        if words1 and words2:
            jaccard_sim = len(words1 & words2) / len(words1 | words2)
        else:
            jaccard_sim = 0.0
        
        # 综合相似度
        combined_sim = sequence_sim * 0.6 + jaccard_sim * 0.4
        
        return combined_sim
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        if not title:
            return ''
        
        # 移除常见的网站后缀
        common_suffixes = [
            r'\s*[-|]\s*.*$',  # 移除用-或|分隔的后缀
            r'\s*\|\s*.*$',
            r'\s*\u00b7\s*.*$',  # 中文间隔符
        ]
        
        cleaned = title.strip()
        for pattern in common_suffixes:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 清理多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned.lower()
    
    def _select_best_bookmark(self, similar_bookmarks: List[Dict]) -> Dict:
        """从相似书签中选择最佳代表"""
        if len(similar_bookmarks) == 1:
            return similar_bookmarks[0]
        
        # 评分标准
        def score_bookmark(bookmark):
            score = 0.0
            
            # 1. 标题质量分（长度和信息量）
            title = bookmark.get('title', '')
            if title:
                score += min(len(title) / 100.0, 0.3)  # 最多0.3分
                
                # 有意义的单词数量
                meaningful_words = len([w for w in title.split() if len(w) > 2])
                score += min(meaningful_words / 10.0, 0.2)  # 最多0.2分
            
            # 2. URL质量分
            url = bookmark.get('url', '')
            if url:
                # 更短的URL通常更好（无跟踪参数）
                if len(url) < 200:
                    score += 0.1
                
                # HTTPS加分
                if url.startswith('https://'):
                    score += 0.1
                
                # 没有跟踪参数加分
                tracking_indicators = ['utm_', 'fbclid', 'gclid', 'ref=']
                if not any(indicator in url for indicator in tracking_indicators):
                    score += 0.2
            
            # 3. 时间新旧度（如果有时间信息）
            add_date = bookmark.get('add_date', '')
            if add_date and add_date.isdigit():
                # 较新的书签加分
                timestamp = int(add_date)
                if timestamp > 1577836800:  # 2020年以后
                    score += 0.1
            
            return score
        
        # 计算每个书签的得分
        scored_bookmarks = [(score_bookmark(b), b) for b in similar_bookmarks]
        
        # 返回得分最高的
        best_score, best_bookmark = max(scored_bookmarks, key=lambda x: x[0])
        
        return best_bookmark
    
    def _get_duplicate_reason(self, original: Dict, duplicate: Dict) -> str:
        """获取重复原因说明"""
        reasons = []
        
        # 检查各种重复类型
        if self._exact_url_match(original, duplicate):
            reasons.append("完全相同URL")
        elif self._normalized_url_match(original, duplicate):
            reasons.append("标准化URL相似")
        
        title_sim = self._calculate_title_similarity(
            original.get('title', ''), duplicate.get('title', '')
        )
        if title_sim >= self.title_threshold:
            reasons.append(f"标题高度相似({title_sim:.2f})")
        
        if not reasons:
            reasons.append("综合相似度较高")
        
        return ", ".join(reasons)
    
    def get_duplicate_statistics(self, duplicates: List[Dict]) -> Dict:
        """获取去重统计信息"""
        stats = {
            'total_duplicates': len(duplicates),
            'duplicate_reasons': defaultdict(int),
            'duplicate_domains': defaultdict(int)
        }
        
        for dup in duplicates:
            reason = dup.get('duplicate_reason', '未知')
            stats['duplicate_reasons'][reason] += 1
            
            url = dup.get('url', '')
            if url:
                try:
                    domain = urlparse(url).netloc
                    stats['duplicate_domains'][domain] += 1
                except Exception:
                    pass
        
        return dict(stats)

# health_checker.py
import requests
import socket
import ssl
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime, timedelta
from enum import Enum

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

class HealthChecker:
    """健康检查器 - 网络连接检测和书签状态验证"""
    
    def __init__(self, timeout: int = 10, max_workers: int = 20, user_agent: str = None):
        self.timeout = timeout
        self.max_workers = max_workers
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # 创建HTTP会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # 设置重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def check_bookmarks(self, bookmarks: List[Dict], parallel: bool = True) -> List[Dict]:
        """检查书签健康状态"""
        if not bookmarks:
            return []
        
        if parallel:
            return self._check_bookmarks_parallel(bookmarks)
        else:
            return self._check_bookmarks_sequential(bookmarks)
    
    def _check_bookmarks_parallel(self, bookmarks: List[Dict]) -> List[Dict]:
        """并行检查书签"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交检查任务
            future_to_bookmark = {
                executor.submit(self._check_single_bookmark, bookmark): bookmark
                for bookmark in bookmarks
            }
            
            # 收集结果
            for future in as_completed(future_to_bookmark):
                bookmark = future_to_bookmark[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # 创建错误结果
                    error_result = self._create_error_result(bookmark, str(e))
                    results.append(error_result)
        
        return results
    
    def _check_bookmarks_sequential(self, bookmarks: List[Dict]) -> List[Dict]:
        """顺序检查书签"""
        results = []
        for bookmark in bookmarks:
            try:
                result = self._check_single_bookmark(bookmark)
                results.append(result)
            except Exception as e:
                error_result = self._create_error_result(bookmark, str(e))
                results.append(error_result)
        return results
    
    def _check_single_bookmark(self, bookmark: Dict) -> Dict:
        """检查单个书签"""
        url = bookmark.get('url', '')
        title = bookmark.get('title', '')
        
        check_result = {
            'url': url,
            'title': title,
            'original_bookmark': bookmark,
            'check_time': datetime.now().isoformat(),
            'status': HealthStatus.UNKNOWN.value,
            'status_code': None,
            'response_time': None,
            'final_url': url,  # 重定向后的最终URL
            'redirect_count': 0,
            'ssl_info': {},
            'content_info': {},
            'errors': [],
            'warnings': []
        }
        
        if not url or not self._is_valid_url(url):
            check_result['status'] = HealthStatus.ERROR.value
            check_result['errors'].append('无效或空URL')
            return check_result
        
        try:
            # 执行健康检查
            start_time = time.time()
            
            # 1. DNS解析检查
            dns_result = self._check_dns(url)
            if not dns_result['success']:
                check_result['status'] = HealthStatus.ERROR.value
                check_result['errors'].extend(dns_result['errors'])
                return check_result
            
            # 2. HTTP请求检查
            http_result = self._check_http(url)
            response_time = time.time() - start_time
            
            # 更新结果
            check_result['response_time'] = round(response_time * 1000, 2)  # 转换为毫秒
            check_result['status_code'] = http_result.get('status_code')
            check_result['final_url'] = http_result.get('final_url', url)
            check_result['redirect_count'] = http_result.get('redirect_count', 0)
            
            # 3. SSL信息检查（HTTPS）
            if url.startswith('https://'):
                ssl_info = self._check_ssl(url)
                check_result['ssl_info'] = ssl_info
            
            # 4. 内容信息检查
            if http_result.get('content'):
                content_info = self._analyze_content(http_result['content'])
                check_result['content_info'] = content_info
            
            # 5. 确定最终状态
            check_result['status'] = self._determine_health_status(
                http_result, check_result
            ).value
            
            # 6. 添加警告
            warnings = self._generate_warnings(http_result, check_result)
            check_result['warnings'] = warnings
            
        except Exception as e:
            check_result['status'] = HealthStatus.ERROR.value
            check_result['errors'].append(f'检查过程出错: {str(e)}')
        
        return check_result
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL有效性"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except Exception:
            return False
    
    def _check_dns(self, url: str) -> Dict:
        """检查DNS解析"""
        result = {'success': False, 'errors': [], 'ip_addresses': []}
        
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc.split(':')[0]  # 移除端口号
            
            # DNS解析
            ip_addresses = socket.getaddrinfo(hostname, None)
            result['ip_addresses'] = list(set([ip[4][0] for ip in ip_addresses]))
            result['success'] = True
            
        except socket.gaierror as e:
            result['errors'].append(f'DNS解析失败: {str(e)}')
        except Exception as e:
            result['errors'].append(f'DNS检查出错: {str(e)}')
        
        return result
    
    def _check_http(self, url: str) -> Dict:
        """检查HTTP连接"""
        result = {
            'success': False,
            'status_code': None,
            'final_url': url,
            'redirect_count': 0,
            'content': None,
            'headers': {},
            'errors': []
        }
        
        try:
            response = self.session.get(
                url, 
                timeout=self.timeout, 
                allow_redirects=True,
                stream=True
            )
            
            result['success'] = True
            result['status_code'] = response.status_code
            result['final_url'] = response.url
            result['redirect_count'] = len(response.history)
            result['headers'] = dict(response.headers)
            
            # 只读取部分内容用于分析
            try:
                content = response.content[:10240]  # 读取前10KB
                result['content'] = content
            except Exception:
                pass
            
        except requests.exceptions.Timeout:
            result['errors'].append(f'请求超时 (>{self.timeout}s)')
        except requests.exceptions.ConnectionError as e:
            result['errors'].append(f'连接错误: {str(e)}')
        except requests.exceptions.RequestException as e:
            result['errors'].append(f'请求异常: {str(e)}')
        except Exception as e:
            result['errors'].append(f'HTTP检查出错: {str(e)}')
        
        return result
    
    def _check_ssl(self, url: str) -> Dict:
        """检查SSL证书信息"""
        ssl_info = {
            'valid': False,
            'expires_at': None,
            'days_until_expiry': None,
            'issuer': None,
            'subject': None,
            'errors': []
        }
        
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc.split(':')[0]
            port = parsed.port or 443
            
            # 获取SSL证书
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    ssl_info['valid'] = True
                    ssl_info['subject'] = dict(x[0] for x in cert['subject'])
                    ssl_info['issuer'] = dict(x[0] for x in cert['issuer'])
                    
                    # 证书过期时间
                    expires_at = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    ssl_info['expires_at'] = expires_at.isoformat()
                    
                    days_until_expiry = (expires_at - datetime.now()).days
                    ssl_info['days_until_expiry'] = days_until_expiry
                    
        except Exception as e:
            ssl_info['errors'].append(f'SSL检查失败: {str(e)}')
        
        return ssl_info
    
    def _analyze_content(self, content: bytes) -> Dict:
        """分析网页内容"""
        content_info = {
            'size': len(content),
            'content_type': None,
            'title': None,
            'has_title_match': False,
            'language': None,
            'encoding': None
        }
        
        try:
            # 尝试检测编码
            import chardet
            detected = chardet.detect(content)
            content_info['encoding'] = detected.get('encoding')
            
            # 解码内容
            text_content = content.decode(content_info['encoding'] or 'utf-8', errors='ignore')
            
            # 提取标题
            import re
            title_match = re.search(r'<title[^>]*>(.*?)</title>', text_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                content_info['title'] = title_match.group(1).strip()
            
            # 检测语言
            lang_match = re.search(r'<html[^>]*lang=["\']([^"\'>]+)["\']', text_content, re.IGNORECASE)
            if lang_match:
                content_info['language'] = lang_match.group(1)
            
        except Exception:
            pass
        
        return content_info
    
    def _determine_health_status(self, http_result: Dict, check_result: Dict) -> HealthStatus:
        """确定健康状态"""
        if not http_result.get('success'):
            return HealthStatus.ERROR
        
        status_code = http_result.get('status_code')
        
        if 200 <= status_code < 300:
            return HealthStatus.HEALTHY
        elif 300 <= status_code < 400:
            return HealthStatus.WARNING  # 重定向
        elif status_code in [404, 410]:  # 页面不存在
            return HealthStatus.ERROR
        elif 400 <= status_code < 500:
            return HealthStatus.WARNING  # 客户端错误
        else:
            return HealthStatus.ERROR  # 服务器错误
    
    def _generate_warnings(self, http_result: Dict, check_result: Dict) -> List[str]:
        """生成警告信息"""
        warnings = []
        
        # 响应时间警告
        response_time = check_result.get('response_time', 0)
        if response_time > 5000:  # 5秒
            warnings.append(f'响应时间过长: {response_time}ms')
        
        # 重定向警告
        redirect_count = check_result.get('redirect_count', 0)
        if redirect_count > 3:
            warnings.append(f'重定向次数过多: {redirect_count}次')
        
        # SSL证书警告
        ssl_info = check_result.get('ssl_info', {})
        if ssl_info.get('days_until_expiry') is not None:
            days = ssl_info['days_until_expiry']
            if days < 30:
                warnings.append(f'SSL证书即将过期: {days}天后')
        
        # 状态码警告
        status_code = check_result.get('status_code')
        if status_code and 300 <= status_code < 400:
            warnings.append(f'页面重定向: HTTP {status_code}')
        elif status_code and 400 <= status_code < 500:
            warnings.append(f'客户端错误: HTTP {status_code}')
        
        return warnings
    
    def _create_error_result(self, bookmark: Dict, error_message: str) -> Dict:
        """创建错误结果"""
        return {
            'url': bookmark.get('url', ''),
            'title': bookmark.get('title', ''),
            'original_bookmark': bookmark,
            'check_time': datetime.now().isoformat(),
            'status': HealthStatus.ERROR.value,
            'status_code': None,
            'response_time': None,
            'final_url': bookmark.get('url', ''),
            'redirect_count': 0,
            'ssl_info': {},
            'content_info': {},
            'errors': [error_message],
            'warnings': []
        }
    
    def get_summary(self, results: List[Dict]) -> Dict:
        """获取检查摘要"""
        if not results:
            return {
                'total_count': 0,
                'accessible_count': 0,
                'error_count': 0,
                'warning_count': 0,
                'average_response_time': 0,
                'status_distribution': {},
                'common_errors': {},
                'slow_bookmarks': [],
                'broken_bookmarks': [],
                'summary': '无书签需要检查'
            }
        
        total_count = len(results)
        status_counts = {}
        response_times = []
        errors = []
        slow_bookmarks = []
        broken_bookmarks = []
        
        for result in results:
            status = result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 收集响应时间
            response_time = result.get('response_time')
            if response_time is not None:
                response_times.append(response_time)
                
                # 识别慢速书签
                if response_time > 3000:  # 3秒
                    slow_bookmarks.append({
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'response_time': response_time
                    })
            
            # 收集错误
            result_errors = result.get('errors', [])
            errors.extend(result_errors)
            
            # 识别损坏的书签
            if result.get('status') == HealthStatus.ERROR.value:
                broken_bookmarks.append({
                    'url': result.get('url'),
                    'title': result.get('title'),
                    'errors': result_errors
                })
        
        # 统计错误类型
        from collections import Counter
        common_errors = dict(Counter(errors).most_common(10))
        
        # 计算平均响应时间
        average_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        accessible_count = status_counts.get('healthy', 0) + status_counts.get('warning', 0)
        error_count = status_counts.get('error', 0)
        warning_count = status_counts.get('warning', 0)
        
        return {
            'total_count': total_count,
            'accessible_count': accessible_count,
            'error_count': error_count,
            'warning_count': warning_count,
            'average_response_time': round(average_response_time, 2),
            'status_distribution': status_counts,
            'common_errors': common_errors,
            'slow_bookmarks': slow_bookmarks[:10],  # 最多显示10个
            'broken_bookmarks': broken_bookmarks[:10],  # 最多显示10个
            'summary': f'检查完成: {accessible_count}/{total_count} 个链接可访问'
        }

# data_exporter.py
import json
import csv
import xml.etree.ElementTree as ET
from typing import Optional, Dict
from xml.dom import minidom
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import re
from .emoji_cleaner import clean_title as clean_emoji_title

class DataExporter:
    """数据导出器 - 支持多种格式的书签导出"""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.supported_formats = ['html', 'json', 'markdown', 'csv', 'xml', 'opml']
        self.export_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def export_html(self, organized_bookmarks: Dict, output_file: str, stats: Optional[Dict] = None):
        """导出HTML格式 - 可导入浏览器"""
        html_content = self._generate_html_content(organized_bookmarks, stats)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html_content(self, organized_bookmarks: Dict, stats: Optional[Dict] = None) -> str:
        """生成符合浏览器收藏夹栏规范的HTML内容，用于完全覆盖"""
        html_parts = []
        
        # HTML标准头部
        html_parts.append('<!DOCTYPE NETSCAPE-Bookmark-file-1>')
        html_parts.append('<!-- This is an automatically generated file.')
        html_parts.append('     It will be read and overwritten.')
        html_parts.append('     DO NOT EDIT! -->')
        html_parts.append('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">')
        html_parts.append('<TITLE>Bookmarks</TITLE>')
        html_parts.append('<H1>Bookmarks</H1>')

        # 添加统计信息注释
        if stats:
            html_parts.append('<!--')
            html_parts.append(f'    Generator: AI智能书签分类系统 v2.0')
            html_parts.append(f'    Export Time: {self.export_timestamp}')
            html_parts.append(f'    Processed Bookmarks: {stats.get("processed_bookmarks", 0)} / {stats.get("total_bookmarks", 0)}')
            
            classifier_stats = stats.get('classifier_stats', {})
            if classifier_stats:
                methods = classifier_stats.get('classification_methods', {})
                if methods:
                    html_parts.append('    Classification Stats:')
                    html_parts.append(f'      - Rule Engine: {methods.get("rule_engine", 0)}')
                    html_parts.append(f'      - ML Classifier: {methods.get("ml_classifier", 0)}')
                    html_parts.append(f'      - Unclassified: {methods.get("unclassified (fallback)", 0)}')
            html_parts.append('-->')

        html_parts.append('<DL><p>')

        # 创建一个“收藏夹栏”文件夹
        # PERSONAL_TOOLBAR_FOLDER="true" 是关键属性
        html_parts.append('    <DT><H3 PERSONAL_TOOLBAR_FOLDER="true">收藏夹栏</H3>')
        html_parts.append('    <DL><p>')

        # 直接在收藏夹栏内生成分类文件夹
        for category, category_data in organized_bookmarks.items():
            html_parts.append(f'        <DT><H3>{self._escape_html(category)}</H3>')
            html_parts.append('        <DL><p>')
            
            # 直接在分类下的书签
            items = category_data.get('_items', [])
            for item in items:
                html_parts.append(self._format_bookmark_html(item, indent='            '))
            
            # 子分类
            subcategories = category_data.get('_subcategories', {})
            for subcat_name, subcat_data in subcategories.items():
                html_parts.append(f'            <DT><H3>{self._escape_html(subcat_name)}</H3>')
                html_parts.append('            <DL><p>')
                
                sub_items = subcat_data.get('_items', [])
                for item in sub_items:
                    html_parts.append(self._format_bookmark_html(item, indent='                '))
                
                html_parts.append('            </DL><p>')
            
            html_parts.append('        </DL><p>')
        
        # 闭合所有标签
        html_parts.append('    </DL><p>') # 闭合收藏夹栏
        html_parts.append('</DL><p>') # 闭合根
        html_parts.append('</HTML>')
        
        return '\n'.join(html_parts)
    
    def _format_bookmark_html(self, item: Dict, indent: str = '        ') -> str:
        """格式HTML书签项"""
        url = self._escape_html(item.get('url', ''))
        title = self._escape_html(item.get('title', '无标题'))
        add_date = item.get('add_date', '')
        confidence = item.get('confidence', 0)
        
        # 构建属性
        attributes = [f'HREF="{url}"']
        if add_date:
            attributes.append(f'ADD_DATE="{add_date}"')
        
        # 添加置信度信息到标题
        confidence_indicator = self._get_confidence_indicator(confidence)
        
        # 使用统一的清理工具，移除开头指示符，避免累加
        clean_title = clean_emoji_title(title)
        
        display_title = f"{confidence_indicator} {clean_title}" if confidence_indicator else clean_title
        
        return f'{indent}<DT><A {" ".join(attributes)}>{display_title}</A>'
    
    def _get_confidence_indicator(self, confidence: float) -> str:
        """获取置信度指示符"""
        if not self.config.get('show_confidence_indicator', True):
            return ''

        if confidence >= 0.9:
            return '🟢'  # 爱心
        elif confidence >= 0.7:
            return '🟡'  # 黄心
        elif confidence >= 0.5:
            return '🟠'  # 橙心
        elif confidence > 0:
            return '🔴'  # 红心
        return ''
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ''
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#x27;'))
    
    def export_json(self, organized_bookmarks: Dict, output_file: str, stats: Optional[Dict] = None):
        """导出JSON格式 - 详细数据"""
        data = {
            'metadata': {
                'export_time': self.export_timestamp,
                'format_version': '2.0',
                'generator': 'AI智能书签分类系统',
                'total_categories': len(organized_bookmarks),
                'total_bookmarks': self._count_total_bookmarks(organized_bookmarks)
            },
            'statistics': stats or {},
            'bookmarks': organized_bookmarks
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def export_markdown(self, organized_bookmarks: Dict, output_file: str, stats: Optional[Dict] = None):
        """导出Markdown格式 - 可读性强"""
        md_content = self._generate_markdown_content(organized_bookmarks, stats)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _generate_markdown_content(self, organized_bookmarks: Dict, stats: Optional[Dict] = None) -> str:
        """生成Markdown内容"""
        lines = []
        
        # 文档头部
        lines.append('# AI智能书签分类报告')
        lines.append('')
        lines.append(f'> 生成时间: {self.export_timestamp}')
        lines.append('')
        
        # 统计信息
        if stats:
            lines.append('## 📊 处理统计')
            lines.append('')
            lines.append(f"- **总书签数**: {stats.get('total_bookmarks', 0)}")
            lines.append(f"- **已处理书签**: {stats.get('processed_bookmarks', 0)}")
            lines.append(f"- **移除重复数**: {stats.get('duplicates_removed', 0)}")
            lines.append(f"- **处理时间**: {stats.get('processing_time', 0):.2f} 秒")
            lines.append(f"- **处理速度**: {stats.get('processing_speed_bps', 0):.2f} 书签/秒")
            lines.append('')

            # 分类方法统计
            classifier_stats = stats.get('classifier_stats', {})
            if classifier_stats:
                lines.append('### 🤖 分类方法统计')
                methods = classifier_stats.get('classification_methods', {})
                if methods:
                    total = methods.get('total', 1)
                    lines.append(f"- **规则引擎**: {methods.get('rule_engine', 0)} ({methods.get('rule_engine', 0) / total:.1%})")
                    lines.append(f"- **机器学习**: {methods.get('ml_classifier', 0)} ({methods.get('ml_classifier', 0) / total:.1%})")
                    lines.append(f"- **未分类**: {methods.get('unclassified (fallback)', 0)} ({methods.get('unclassified (fallback)', 0) / total:.1%})")
                lines.append(f"- **平均置信度**: {classifier_stats.get('average_confidence', 0):.2f}")
                lines.append('')

            # 分类分布
            categories_found = stats.get('categories_found', {})
            if categories_found:
                lines.append(f"### 📁 分类分布")
                for category, count in sorted(categories_found.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"  - {category}: {count} 个")
            
            lines.append('')
        
        # 目录
        lines.append('## 📚 目录')
        lines.append('')
        for i, category in enumerate(organized_bookmarks.keys(), 1):
            lines.append(f"{i}. [{category}](#{self._slugify(category)})")
        lines.append('')
        
        # 分类内容
        for category, category_data in organized_bookmarks.items():
            lines.append(f'## {category}')
            lines.append('')
            
            # 直接在分类下的书签
            items = category_data.get('_items', [])
            if items:
                for item in items:
                    lines.append(self._format_bookmark_markdown(item))
                lines.append('')
            
            # 子分类
            subcategories = category_data.get('_subcategories', {})
            for subcat_name, subcat_data in subcategories.items():
                lines.append(f'### {subcat_name}')
                lines.append('')
                
                sub_items = subcat_data.get('_items', [])
                for item in sub_items:
                    lines.append(self._format_bookmark_markdown(item))
                lines.append('')
        
        # 页脚
        lines.append('---')
        lines.append(f'*由 AI智能书签分类系统 v2.0 生成 - {self.export_timestamp}*')
        
        return '\n'.join(lines)
    
    def _format_bookmark_markdown(self, item: Dict) -> str:
        """格式Markdown书签项"""
        url = item.get('url', '')
        title = item.get('title', '无标题')
        confidence = item.get('confidence', 0)
        
        # 置信度指示
        confidence_indicator = self._get_confidence_indicator(confidence)
        confidence_text = f" ({confidence:.2f})" if confidence > 0 else ""
        # 清理冒头重复 emoji 前缀（统一工具）
        clean_title = clean_emoji_title(title)
        prefix = f"{confidence_indicator} " if confidence_indicator else ""
        return f"- {prefix}[{clean_title}]({url}){confidence_text}"
    
    def _slugify(self, text: str) -> str:
        """将文本转换为适合作Markdown锦点的格式"""
        # 简单的slug化处理
        slug = re.sub(r'[^\w\s-]', '', text).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug
    
    def export_csv(self, organized_bookmarks: Dict, output_file: str, stats: Optional[Dict] = None):
        """导出CSV格式 - 适合数据分析"""
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                'category', 'subcategory', 'title', 'url', 'confidence', 
                'method', 'add_date', 'source_file'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 写入头部
            writer.writeheader()
            
            # 写入数据
            for category, category_data in organized_bookmarks.items():
                # 直接在分类下的书签
                items = category_data.get('_items', [])
                for item in items:
                    writer.writerow({
                        'category': category,
                        'subcategory': '',
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'confidence': item.get('confidence', 0),
                        'method': item.get('method', ''),
                        'add_date': item.get('add_date', ''),
                        'source_file': item.get('source_file', '')
                    })
                
                # 子分类
                subcategories = category_data.get('_subcategories', {})
                for subcat_name, subcat_data in subcategories.items():
                    sub_items = subcat_data.get('_items', [])
                    for item in sub_items:
                        writer.writerow({
                            'category': category,
                            'subcategory': subcat_name,
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'confidence': item.get('confidence', 0),
                            'method': item.get('method', ''),
                            'add_date': item.get('add_date', ''),
                            'source_file': item.get('source_file', '')
                        })
    
    def export_xml(self, organized_bookmarks: Dict, output_file: str, stats: Optional[Dict] = None):
        """导出XML格式 - 结构化数据"""
        root = ET.Element('bookmarks')
        root.set('version', '2.0')
        root.set('generator', 'AI智能书签分类系统')
        root.set('export_time', self.export_timestamp)
        
        # 添加统计信息
        if stats:
            stats_elem = ET.SubElement(root, 'statistics')
            for key, value in stats.items():
                if isinstance(value, dict):
                    dict_elem = ET.SubElement(stats_elem, key)
                    for sub_key, sub_value in value.items():
                        sub_elem = ET.SubElement(dict_elem, 'item')
                        sub_elem.set('name', str(sub_key))
                        sub_elem.text = str(sub_value)
                else:
                    stat_elem = ET.SubElement(stats_elem, key)
                    stat_elem.text = str(value)
        
        # 添加书签数据
        bookmarks_elem = ET.SubElement(root, 'categories')
        
        for category, category_data in organized_bookmarks.items():
            category_elem = ET.SubElement(bookmarks_elem, 'category')
            category_elem.set('name', category)
            
            # 直接在分类下的书签
            items = category_data.get('_items', [])
            if items:
                items_elem = ET.SubElement(category_elem, 'items')
                for item in items:
                    self._add_bookmark_xml(items_elem, item)
            
            # 子分类
            subcategories = category_data.get('_subcategories', {})
            if subcategories:
                subcats_elem = ET.SubElement(category_elem, 'subcategories')
                for subcat_name, subcat_data in subcategories.items():
                    subcat_elem = ET.SubElement(subcats_elem, 'subcategory')
                    subcat_elem.set('name', subcat_name)
                    
                    sub_items = subcat_data.get('_items', [])
                    if sub_items:
                        sub_items_elem = ET.SubElement(subcat_elem, 'items')
                        for item in sub_items:
                            self._add_bookmark_xml(sub_items_elem, item)
        
        # 格式化并写入文件
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
    
    def _add_bookmark_xml(self, parent: ET.Element, item: Dict):
        """添加书签XML元素"""
        bookmark_elem = ET.SubElement(parent, 'bookmark')
        
        # 必需属性
        bookmark_elem.set('url', item.get('url', ''))
        bookmark_elem.set('title', item.get('title', ''))
        
        # 可选属性
        if item.get('confidence'):
            bookmark_elem.set('confidence', str(item['confidence']))
        if item.get('method'):
            bookmark_elem.set('method', item['method'])
        if item.get('add_date'):
            bookmark_elem.set('add_date', item['add_date'])
        if item.get('source_file'):
            bookmark_elem.set('source_file', item['source_file'])
    
    def export_opml(self, organized_bookmarks: Dict, output_file: str, stats: Optional[Dict] = None):
        """导出OPML格式 - RSS/阅读器兼容"""
        root = ET.Element('opml')
        root.set('version', '2.0')
        
        # 头部信息
        head = ET.SubElement(root, 'head')
        ET.SubElement(head, 'title').text = 'AI智能书签分类结果'
        ET.SubElement(head, 'dateCreated').text = self.export_timestamp
        ET.SubElement(head, 'generator').text = 'AI智能书签分类系统 v2.0'
        
        # 主体内容
        body = ET.SubElement(root, 'body')
        
        for category, category_data in organized_bookmarks.items():
            category_outline = ET.SubElement(body, 'outline')
            category_outline.set('text', category)
            category_outline.set('title', category)
            
            # 直接在分类下的书签
            items = category_data.get('_items', [])
            for item in items:
                item_outline = ET.SubElement(category_outline, 'outline')
                item_outline.set('text', item.get('title', ''))
                item_outline.set('title', item.get('title', ''))
                item_outline.set('type', 'link')
                item_outline.set('url', item.get('url', ''))
            
            # 子分类
            subcategories = category_data.get('_subcategories', {})
            for subcat_name, subcat_data in subcategories.items():
                subcat_outline = ET.SubElement(category_outline, 'outline')
                subcat_outline.set('text', subcat_name)
                subcat_outline.set('title', subcat_name)
                
                sub_items = subcat_data.get('_items', [])
                for item in sub_items:
                    item_outline = ET.SubElement(subcat_outline, 'outline')
                    item_outline.set('text', item.get('title', ''))
                    item_outline.set('title', item.get('title', ''))
                    item_outline.set('type', 'link')
                    item_outline.set('url', item.get('url', ''))
        
        # 格式化并写入文件
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
    
    def _count_total_bookmarks(self, organized_bookmarks: Dict) -> int:
        """计算总书签数量"""
        total = 0
        for category_data in organized_bookmarks.values():
            # 直接书签
            total += len(category_data.get('_items', []))
            
            # 子分类书签
            subcategories = category_data.get('_subcategories', {})
            for subcat_data in subcategories.values():
                total += len(subcat_data.get('_items', []))
        
        return total
    
    def export_all_formats(self, organized_bookmarks: Dict, output_dir: str, 
                          base_filename: str = 'bookmarks', stats: Optional[Dict] = None):
        """导出所有支持的格式"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        export_methods = {
            'html': self.export_html,
            'json': self.export_json,
            'markdown': self.export_markdown,
            'csv': self.export_csv,
            'xml': self.export_xml,
            'opml': self.export_opml
        }
        
        exported_files = []
        
        for format_name, export_method in export_methods.items():
            try:
                output_file = os.path.join(output_dir, f"{base_filename}_{timestamp}.{format_name}")
                export_method(organized_bookmarks, output_file, stats)
                exported_files.append(output_file)
            except Exception as e:
                print(f"警告: 导出{format_name}格式失败: {e}")
        
        return exported_files

# 在ai_classifier.py中需要的导入
from datetime import datetime