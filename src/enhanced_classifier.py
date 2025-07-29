"""
Enhanced Bookmark Classification System - 增强版书签分类系统

核心改进：
1. 动态权重调整算法
2. 智能上下文感知分类
3. 多维度特征融合
4. 自适应学习机制
5. 高效缓存系统
"""

import os
import json
import re
import time
from typing import Dict, List, Tuple, Optional, Set
from urllib.parse import urlparse
from collections import defaultdict, Counter
from functools import lru_cache
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# 导入机器学习分类器
try:
    from ml_classifier import MLClassifierWrapper
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@dataclass
class EnhancedBookmarkFeatures:
    """增强的书签特征提取"""
    url: str
    title: str
    domain: str
    path_segments: List[str]
    query_params: Dict[str, str]
    content_type: str
    language: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 计算特征
    domain_depth: int = 0
    path_depth: int = 0
    title_length: int = 0
    has_numbers: bool = False
    is_secure: bool = False
    
    def __post_init__(self):
        self.domain_depth = len(self.domain.split('.'))
        self.path_depth = len(self.path_segments)
        self.title_length = len(self.title)
        self.has_numbers = bool(re.search(r'\d', self.title))
        self.is_secure = self.url.startswith('https://')

@dataclass
class ClassificationResult:
    """分类结果"""
    category: str
    confidence: float
    score_breakdown: Dict[str, float]
    alternative_categories: List[Tuple[str, float]]
    reasoning: List[str]
    processing_time: float = 0.0
    features_used: List[str] = field(default_factory=list)

class EnhancedClassifier:
    """增强版分类器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logger()
        
        # 缓存系统
        self.url_cache = {}
        self.classification_cache = {}
        self.feature_cache = {}
        
        # 统计信息
        self.stats = {
            'total_classified': 0,
            'cache_hits': 0,
            'avg_processing_time': 0.0,
            'category_distribution': Counter(),
            'confidence_distribution': defaultdict(int)
        }
        
        # 学习系统
        self.learning_weights = defaultdict(float)
        self.category_patterns = defaultdict(set)
        self.temporal_patterns = defaultdict(list)
        
        # 机器学习分类器
        self.ml_classifier = None
        if ML_AVAILABLE:
            self.ml_classifier = MLClassifierWrapper()
        
        # 预编译正则表达式
        self._compile_patterns()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger(f"{__name__}.{id(self)}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """默认配置"""
        return {
            "category_rules": {},
            "priority_rules": {},
            "title_cleaning_rules": {},
            "advanced_settings": {
                "classification_threshold": 0.6,
                "learning_rate": 0.1,
                "cache_size": 10000,
                "confidence_boost_factor": 1.2
            }
        }
    
    def _compile_patterns(self):
        """预编译正则表达式模式"""
        self.compiled_patterns = {}
        
        # 常用模式
        patterns = {
            'github_repo': r'github\.com/[\w-]+/[\w-]+',
            'video_id': r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)',
            'article_path': r'/(?:article|post|blog)/[\w-]+',
            'api_endpoint': r'/api/v?\d+/',
            'file_extension': r'\.(\w+)$',
            'version_number': r'v?\d+\.\d+(?:\.\d+)?',
            'chinese_chars': r'[\u4e00-\u9fff]+',
            'numeric_id': r'\d{3,}'
        }
        
        for name, pattern in patterns.items():
            try:
                self.compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                self.logger.warning(f"Failed to compile pattern {name}: {e}")
    
    @lru_cache(maxsize=50000)
    def _parse_url_cached(self, url: str) -> urlparse:
        """缓存的URL解析"""
        return urlparse(url)
    
    def extract_features(self, url: str, title: str) -> EnhancedBookmarkFeatures:
        """增强的特征提取"""
        cache_key = f"{url}::{title}"
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        try:
            parsed = self._parse_url_cached(url)
            domain = parsed.netloc.lower().replace('www.', '')
            path_segments = [seg for seg in parsed.path.split('/') if seg]
            
            # 查询参数解析
            query_params = {}
            if parsed.query:
                for param in parsed.query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            # 内容类型检测
            content_type = self._detect_content_type(url, title, path_segments)
            
            # 语言检测
            language = self._detect_language(title)
            
            features = EnhancedBookmarkFeatures(
                url=url,
                title=title,
                domain=domain,
                path_segments=path_segments,
                query_params=query_params,
                content_type=content_type,
                language=language
            )
            
            # 缓存结果
            if len(self.feature_cache) < self.config.get('advanced_settings', {}).get('cache_size', 10000):
                self.feature_cache[cache_key] = features
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed for {url}: {e}")
            return EnhancedBookmarkFeatures(
                url=url, title=title, domain="", path_segments=[], 
                query_params={}, content_type="unknown", language="unknown"
            )
    
    def _detect_content_type(self, url: str, title: str, path_segments: List[str]) -> str:
        """智能内容类型检测"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # 使用预编译的正则表达式
        if self.compiled_patterns.get('github_repo', re.compile(r'')).search(url_lower):
            if any(keyword in path_segments for keyword in ['issues', 'pull', 'releases']):
                return 'github_management'
            return 'github_code'
        
        if self.compiled_patterns.get('video_id', re.compile(r'')).search(url_lower):
            return 'video'
        
        if self.compiled_patterns.get('api_endpoint', re.compile(r'')).search(url_lower):
            return 'api_docs'
        
        # 基于扩展名检测
        if path_segments:
            last_segment = path_segments[-1]
            if '.' in last_segment:
                ext = last_segment.split('.')[-1].lower()
                type_map = {
                    'pdf': 'document',
                    'doc': 'document', 'docx': 'document',
                    'ppt': 'presentation', 'pptx': 'presentation',
                    'jpg': 'image', 'png': 'image', 'gif': 'image',
                    'mp4': 'video', 'avi': 'video',
                    'zip': 'archive', 'rar': 'archive'
                }
                if ext in type_map:
                    return type_map[ext]
        
        # 基于标题和域名检测
        type_indicators = {
            'tutorial': ['tutorial', 'guide', '教程', '指南', 'how-to'],
            'news': ['news', 'article', '新闻', '文章', 'blog'],
            'tool': ['tool', 'online', 'generator', '工具', '在线'],
            'documentation': ['docs', 'documentation', 'reference', 'manual', '文档'],
            'forum': ['forum', 'community', '论坛', '社区', 'discussion'],
            'shopping': ['shop', 'buy', 'store', '购买', '商店', 'price'],
            'social': ['social', 'share', '分享', 'community', 'follow']
        }
        
        for content_type, keywords in type_indicators.items():
            if any(keyword in title_lower or keyword in url_lower for keyword in keywords):
                return content_type
        
        return 'webpage'
    
    def _detect_language(self, title: str) -> str:
        """语言检测"""
        if not title:
            return 'unknown'
        
        # 检测中文字符
        if self.compiled_patterns.get('chinese_chars', re.compile(r'')).search(title):
            return 'zh'
        
        # 简单的语言检测
        common_english_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = set(re.findall(r'\b\w+\b', title.lower()))
        
        if len(words & common_english_words) > 0:
            return 'en'
        
        return 'unknown'
    
    def classify(self, url: str, title: str, context: Optional[Dict] = None) -> ClassificationResult:
        """主分类方法"""
        start_time = time.time()
        
        # 检查缓存
        cache_key = f"{url}::{title}"
        if cache_key in self.classification_cache:
            self.stats['cache_hits'] += 1
            cached_result = self.classification_cache[cache_key]
            cached_result.processing_time = time.time() - start_time
            return cached_result
        
        try:
            # 特征提取
            features = self.extract_features(url, title)
            
            # 多维度评分
            scores = defaultdict(float)
            reasoning = []
            features_used = []
            
            # 1. 优先级规则评分
            priority_scores = self._apply_priority_rules(features)
            for category, score in priority_scores.items():
                scores[category] += score
                if score > 0:
                    reasoning.append(f"优先级规则匹配: {category} (+{score:.2f})")
                    features_used.append("priority_rules")
            
            # 2. 常规分类规则评分
            category_scores = self._apply_category_rules(features)
            for category, score in category_scores.items():
                scores[category] += score
                if score > 0:
                    reasoning.append(f"分类规则匹配: {category} (+{score:.2f})")
                    features_used.append("category_rules")
            
            # 3. 上下文感知评分
            context_scores = self._apply_context_rules(features, context)
            for category, score in context_scores.items():
                scores[category] += score
                if score > 0:
                    reasoning.append(f"上下文感知: {category} (+{score:.2f})")
                    features_used.append("context_rules")
            
            # 4. 学习权重调整
            learning_scores = self._apply_learning_weights(features)
            for category, score in learning_scores.items():
                scores[category] += score
                if score > 0:
                    reasoning.append(f"学习权重: {category} (+{score:.2f})")
                    features_used.append("learning_weights")
            
            # 5. 时间模式评分
            temporal_scores = self._apply_temporal_patterns(features)
            for category, score in temporal_scores.items():
                scores[category] += score
                if score > 0:
                    reasoning.append(f"时间模式: {category} (+{score:.2f})")
                    features_used.append("temporal_patterns")
            
            # 6. 机器学习分类
            if self.ml_classifier:
                ml_result = self.ml_classifier.classify(features, context)
                if ml_result:
                    ml_category = ml_result['category']
                    ml_confidence = ml_result['confidence']
                    ml_score = ml_confidence * 10  # 将置信度转换为分数
                    scores[ml_category] += ml_score
                    reasoning.append(f"机器学习: {ml_category} (+{ml_score:.2f})")
                    features_used.append("machine_learning")
            
            # 归一化和选择最佳分类
            if not scores:
                result = ClassificationResult(
                    category="未分类",
                    confidence=0.0,
                    score_breakdown={},
                    alternative_categories=[],
                    reasoning=["没有匹配的分类规则"],
                    features_used=features_used
                )
            else:
                # 计算置信度
                total_score = sum(scores.values())
                normalized_scores = {cat: score/total_score for cat, score in scores.items()}
                
                # 选择最佳分类
                best_category = max(normalized_scores, key=normalized_scores.get)
                confidence = normalized_scores[best_category]
                
                # 应用置信度提升因子
                boost_factor = self.config.get('advanced_settings', {}).get('confidence_boost_factor', 1.0)
                if confidence > 0.7:
                    confidence = min(1.0, confidence * boost_factor)
                
                # 备选分类
                alternatives = [(cat, score) for cat, score in normalized_scores.items() 
                              if cat != best_category]
                alternatives.sort(key=lambda x: x[1], reverse=True)
                
                result = ClassificationResult(
                    category=best_category,
                    confidence=confidence,
                    score_breakdown=dict(normalized_scores),
                    alternative_categories=alternatives[:5],
                    reasoning=reasoning,
                    features_used=list(set(features_used))
                )
            
            # 记录处理时间
            result.processing_time = time.time() - start_time
            
            # 更新统计信息
            self._update_stats(result)
            
            # 缓存结果
            if len(self.classification_cache) < self.config.get('advanced_settings', {}).get('cache_size', 10000):
                self.classification_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Classification failed for {url}: {e}")
            return ClassificationResult(
                category="未分类",
                confidence=0.0,
                score_breakdown={},
                alternative_categories=[],
                reasoning=[f"分类失败: {str(e)}"],
                processing_time=time.time() - start_time
            )
    
    def _apply_priority_rules(self, features: EnhancedBookmarkFeatures) -> Dict[str, float]:
        """应用优先级规则"""
        scores = defaultdict(float)
        priority_rules = self.config.get("priority_rules", {})
        
        for category, rule_data in priority_rules.items():
            base_weight = rule_data.get("weight", 100)
            rules = rule_data.get("rules", [])
            
            for rule in rules:
                score = self._evaluate_enhanced_rule(rule, features, base_weight)
                if score > 0:
                    scores[category] += score
        
        return scores
    
    def _apply_category_rules(self, features: EnhancedBookmarkFeatures) -> Dict[str, float]:
        """应用分类规则"""
        scores = defaultdict(float)
        category_rules = self.config.get("category_rules", {})
        
        for category, rule_data in category_rules.items():
            rules = rule_data.get("rules", [])
            
            for rule in rules:
                base_weight = rule.get("weight", 5)
                score = self._evaluate_enhanced_rule(rule, features, base_weight)
                if score > 0:
                    scores[category] += score
        
        return scores
    
    def _apply_context_rules(self, features: EnhancedBookmarkFeatures, context: Optional[Dict]) -> Dict[str, float]:
        """应用上下文感知规则"""
        scores = defaultdict(float)
        
        if not context:
            return scores
        
        # 基于时间的上下文
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # 工作时间
            if any(work_indicator in features.domain for work_indicator in ['github.com', 'stackoverflow.com']):
                scores["技术栈"] += 2.0
        
        # 基于内容类型的上下文增强
        content_boost = {
            'github_code': {"技术栈": 3.0},
            'video': {"娱乐": 2.0, "学习": 1.5},
            'documentation': {"技术资料": 2.5},
            'tutorial': {"学习": 2.0, "技术资料": 1.5}
        }
        
        if features.content_type in content_boost:
            for category, boost in content_boost[features.content_type].items():
                scores[category] += boost
        
        return scores
    
    def _apply_learning_weights(self, features: EnhancedBookmarkFeatures) -> Dict[str, float]:
        """应用学习权重"""
        scores = defaultdict(float)
        
        # 基于域名的学习权重
        if features.domain in self.learning_weights:
            # 查找该域名通常被分类到的类别
            for category in self.category_patterns:
                if features.domain in self.category_patterns[category]:
                    scores[category] += self.learning_weights[features.domain]
        
        return scores
    
    def _apply_temporal_patterns(self, features: EnhancedBookmarkFeatures) -> Dict[str, float]:
        """应用时间模式"""
        scores = defaultdict(float)
        
        # 分析最近的分类模式
        current_time = datetime.now()
        for category, timestamps in self.temporal_patterns.items():
            recent_count = sum(1 for ts in timestamps 
                             if current_time - ts < timedelta(hours=24))
            if recent_count > 5:  # 最近24小时内该类别很活跃
                scores[category] += 1.0
        
        return scores
    
    def _evaluate_enhanced_rule(self, rule: Dict, features: EnhancedBookmarkFeatures, base_weight: float) -> float:
        """增强的规则评估"""
        match_type = rule.get("match", "")
        keywords = rule.get("keywords", [])
        weight = rule.get("weight", base_weight)
        exclusions = rule.get("must_not_contain", [])
        
        if not keywords:
            return 0.0
        
        # 获取匹配目标
        target_text = ""
        if match_type == "domain":
            target_text = features.domain
        elif match_type == "title":
            target_text = features.title.lower()
        elif match_type == "url":
            target_text = features.url.lower()
        elif match_type == "path":
            target_text = " ".join(features.path_segments).lower()
        elif match_type == "content_type":
            target_text = features.content_type
        
        if not target_text:
            return 0.0
        
        # 计算匹配分数
        max_score = 0.0
        for keyword in keywords:
            score = self._calculate_match_score(keyword.lower(), target_text, features)
            max_score = max(max_score, score)
        
        # 应用排除规则
        for exclusion in exclusions:
            if exclusion.lower() in target_text:
                max_score *= 0.1  # 严重惩罚
                break
        
        # 应用增强因子
        enhanced_score = max_score * weight
        
        # 基于特征的动态调整
        if features.content_type != "unknown":
            enhanced_score *= 1.1  # 已知内容类型的轻微提升
        
        if features.is_secure:
            enhanced_score *= 1.05  # HTTPS站点的轻微提升
        
        return enhanced_score
    
    def _calculate_match_score(self, keyword: str, target_text: str, features: EnhancedBookmarkFeatures) -> float:
        """计算匹配分数"""
        if keyword in target_text:
            # 精确匹配
            if target_text == keyword:
                return 1.0
            
            # 词边界匹配
            if re.search(rf'\b{re.escape(keyword)}\b', target_text):
                return 0.9
            
            # 包含匹配
            return 0.7
        
        # 模糊匹配（仅对于某些情况）
        if len(keyword) > 3:
            # 编辑距离匹配
            similarity = self._calculate_similarity(keyword, target_text)
            if similarity > 0.8:
                return similarity * 0.6
        
        return 0.0
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度（简化版）"""
        if not s1 or not s2:
            return 0.0
        
        # Jaccard相似度
        set1 = set(s1.lower())
        set2 = set(s2.lower())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _update_stats(self, result: ClassificationResult):
        """更新统计信息"""
        self.stats['total_classified'] += 1
        self.stats['category_distribution'][result.category] += 1
        
        # 更新平均处理时间
        total_time = self.stats['avg_processing_time'] * (self.stats['total_classified'] - 1)
        self.stats['avg_processing_time'] = (total_time + result.processing_time) / self.stats['total_classified']
        
        # 置信度分布
        confidence_range = int(result.confidence * 10) / 10
        self.stats['confidence_distribution'][confidence_range] += 1
    
    def learn_from_feedback(self, url: str, title: str, correct_category: str, predicted_category: str):
        """从反馈中学习"""
        features = self.extract_features(url, title)
        
        # 更新学习权重
        learning_rate = self.config.get('advanced_settings', {}).get('learning_rate', 0.1)
        
        if predicted_category != correct_category:
            # 惩罚错误预测
            self.learning_weights[features.domain] -= learning_rate
            
            # 奖励正确类别
            self.category_patterns[correct_category].add(features.domain)
            self.learning_weights[features.domain] += learning_rate * 2
        else:
            # 强化正确预测
            self.learning_weights[features.domain] += learning_rate * 0.5
        
        # 更新时间模式
        self.temporal_patterns[correct_category].append(datetime.now())
        
        # 保持最近的100个时间戳
        if len(self.temporal_patterns[correct_category]) > 100:
            self.temporal_patterns[correct_category] = self.temporal_patterns[correct_category][-100:]
        
        # 机器学习在线学习
        if self.ml_classifier:
            self.ml_classifier.ml_classifier.online_learn(
                {
                    'url': url,
                    'title': title,
                    'domain': features.domain,
                    'path_segments': features.path_segments,
                    'content_type': features.content_type,
                    'language': features.language
                },
                correct_category
            )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            **self.stats,
            'cache_size': len(self.classification_cache),
            'feature_cache_size': len(self.feature_cache),
            'learning_weights_count': len(self.learning_weights),
            'category_patterns_count': len(self.category_patterns)
        }
        
        # 添加ML分类器统计信息
        if self.ml_classifier:
            stats['ml_classifier'] = self.ml_classifier.get_stats()
        
        return stats
    
    def clear_cache(self):
        """清除缓存"""
        self.classification_cache.clear()
        self.feature_cache.clear()
        self.url_cache.clear()
        self.logger.info("缓存已清除")
    
    def save_learning_data(self, path: str = "models/learning_data.json"):
        """保存学习数据"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        learning_data = {
            'learning_weights': dict(self.learning_weights),
            'category_patterns': {k: list(v) for k, v in self.category_patterns.items()},
            'temporal_patterns': {
                k: [ts.isoformat() for ts in v] 
                for k, v in self.temporal_patterns.items()
            },
            'stats': self.stats,
            'last_update': datetime.now().isoformat()
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(learning_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"学习数据已保存到: {path}")
    
    def load_learning_data(self, path: str = "models/learning_data.json"):
        """加载学习数据"""
        if not os.path.exists(path):
            self.logger.info("学习数据文件不存在，使用默认设置")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                learning_data = json.load(f)
            
            self.learning_weights = defaultdict(float, learning_data.get('learning_weights', {}))
            
            self.category_patterns = defaultdict(set)
            for k, v in learning_data.get('category_patterns', {}).items():
                self.category_patterns[k] = set(v)
            
            self.temporal_patterns = defaultdict(list)
            for k, v in learning_data.get('temporal_patterns', {}).items():
                self.temporal_patterns[k] = [datetime.fromisoformat(ts) for ts in v]
            
            if 'stats' in learning_data:
                self.stats.update(learning_data['stats'])
            
            self.logger.info(f"学习数据已从 {path} 加载")
            
        except Exception as e:
            self.logger.error(f"加载学习数据失败: {e}")