"""
AI Bookmark Classifier Core
AI书签分类器核心模块

集成了多种AI技术的智能书签分类器：
- 基于规则的快速匹配
- 机器学习模型预测
- 深度学习语义理解
- 用户行为学习
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import hashlib
import re
from urllib.parse import urlparse

# 导入子模块
try:
    from .ml_classifier import MLClassifierWrapper
except ImportError:
    MLClassifierWrapper = None

# LLM 分类器
try:
    from .llm_classifier import LLMClassifier
except ImportError:
    LLMClassifier = None

from .rule_engine import RuleEngine

# 导入占位符模块
from .placeholder_modules import (
    SemanticAnalyzer, UserProfiler, PerformanceMonitor
)

@dataclass
class BookmarkFeatures:
    """书签特征"""
    url: str
    title: str
    domain: str
    path_segments: List[str]
    query_params: Dict[str, str]
    content_type: str
    language: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 计算特征
    @property
    def url_length(self) -> int:
        return len(self.url)
    
    @property
    def title_length(self) -> int:
        return len(self.title)
    
    @property
    def is_secure(self) -> bool:
        return self.url.startswith('https://')
    
    @property
    def has_chinese(self) -> bool:
        return bool(re.search(r'[\u4e00-\u9fff]', self.title))

@dataclass
class ClassificationResult:
    """分类结果"""
    category: str
    confidence: float
    subcategory: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    processing_time: float = 0.0
    method: str = "unknown"

class AIBookmarkClassifier:
    """AI智能书签分类器"""
    
    def __init__(self, config_path: str = "config.json", enable_ml: bool = True):
        self.config_path = config_path
        self.enable_ml = enable_ml
        self.logger = logging.getLogger(__name__)
        
        # 延迟初始化组件以提高启动性能
        self._config = None
        self._rule_engine = None
        self._semantic_analyzer = None
        self._user_profiler = None
        self._performance_monitor = None
        self._ml_classifier = None
        self._llm_classifier = None
        
        # 缓存系统 - 优化缓存大小和策略
        self.feature_cache = {}
        self.classification_cache = {}
        self._max_cache_size = 5000
        
        # 统计信息
        self.stats = {
            'total_classified': 0,
            'rule_engine': 0,
            'ml_classifier': 0,
            'semantic_analyzer': 0,
            'user_profiler': 0,
            'fallback': 0, # 未分类
            'cache_hits': 0,
            'average_confidence': 0.0,
            'llm': 0
        }
    
    @property
    def config(self):
        """延迟加载配置"""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    @property 
    def rule_engine(self):
        """延迟加载规则引擎"""
        if self._rule_engine is None:
            self._rule_engine = RuleEngine(self.config)
        return self._rule_engine
    
    @property
    def semantic_analyzer(self):
        """延迟加载语义分析器"""
        if self._semantic_analyzer is None:
            self._semantic_analyzer = SemanticAnalyzer()
        return self._semantic_analyzer
    
    @property
    def user_profiler(self):
        """延迟加载用户画像"""
        if self._user_profiler is None:
            self._user_profiler = UserProfiler()
        return self._user_profiler
    
    @property
    def performance_monitor(self):
        """延迟加载性能监控"""
        if self._performance_monitor is None:
            self._performance_monitor = PerformanceMonitor()
        return self._performance_monitor
    
    @property
    def ml_classifier(self):
        """延迟加载ML分类器"""
        if self._ml_classifier is None and self.enable_ml:
            try:
                self._ml_classifier = MLClassifierWrapper()
                self.logger.info("机器学习组件已启用")
            except Exception as e:
                self.logger.warning(f"机器学习组件初始化失败: {e}")
        return self._ml_classifier
    
    @property
    def llm_classifier(self):
        """延迟加载LLM分类器（按配置启用）"""
        if self._llm_classifier is None and LLMClassifier is not None:
            try:
                self._llm_classifier = LLMClassifier(self.config_path)
            except Exception as e:
                self.logger.warning(f"LLM 分类器初始化失败: {e}")
        return self._llm_classifier
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """默认配置"""
        return {
            "ai_settings": {
                "confidence_threshold": 0.7,
                "use_semantic_analysis": True,
                "use_user_profiling": True,
                "cache_size": 10000
            },
            "category_rules": {
                "AI/机器学习": {
                    "rules": [
                        {"match": "domain", "keywords": ["openai.com", "huggingface.co"], "weight": 20},
                        {"match": "title", "keywords": ["machine learning", "深度学习", "neural", "AI"], "weight": 15}
                    ]
                },
                "技术/编程": {
                    "rules": [
                        {"match": "domain", "keywords": ["github.com", "stackoverflow.com"], "weight": 20},
                        {"match": "title", "keywords": ["programming", "code", "编程", "代码"], "weight": 10}
                    ]
                }
            },
            "category_hierarchy": {
                "AI": ["机器学习", "深度学习", "自然语言处理", "计算机视觉"],
                "技术": ["编程", "前端", "后端", "DevOps", "数据库"],
                "学习": ["教程", "文档", "课程", "书籍"],
                "工具": ["在线工具", "开发工具", "设计工具"]
            }
        }
    
    def extract_features(self, url: str, title: str) -> BookmarkFeatures:
        """提取书签特征"""
        cache_key = f"{url}::{title}"
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            path_segments = [seg for seg in parsed.path.split('/') if seg]
            
            # 解析查询参数
            query_params = {}
            if parsed.query:
                for param in parsed.query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            # 内容类型检测
            content_type = self._detect_content_type(url, title)
            
            # 语言检测
            language = self._detect_language(title)
            
            features = BookmarkFeatures(
                url=url,
                title=title,
                domain=domain,
                path_segments=path_segments,
                query_params=query_params,
                content_type=content_type,
                language=language
            )
            
            # 缓存特征
            if len(self.feature_cache) < self.config.get('ai_settings', {}).get('cache_size', 10000):
                self.feature_cache[cache_key] = features
            
            return features
            
        except Exception as e:
            self.logger.error(f"特征提取失败 {url}: {e}")
            return BookmarkFeatures(
                url=url, title=title, domain="", path_segments=[],
                query_params={}, content_type="unknown", language="unknown"
            )
    
    def classify(self, url: str, title: str) -> ClassificationResult:
        """优化的智能分类主方法"""
        start_time = datetime.now()
        
        # 检查缓存
        cache_key = hashlib.md5(f"{url}::{title}".encode()).hexdigest()
        if cache_key in self.classification_cache:
            self.stats['cache_hits'] += 1
            cached_result = self.classification_cache[cache_key]
            cached_result.processing_time = (datetime.now() - start_time).total_seconds()
            return cached_result
        
        # 提取特征
        features = self.extract_features(url, title)
        
        # 多方法分类和融合
        results = []

        # 1. 规则引擎分类
        rule_result = self.rule_engine.classify(features)
        if rule_result:
            results.append(rule_result)
        
        # 2. 机器学习分类
        if self.ml_classifier:
            # 直接传递特征对象，包装器会处理它
            ml_result = self.ml_classifier.classify(features)
            if ml_result:
                results.append(ml_result)

        # 3. 语义分析
        if self.config.get('ai_settings', {}).get('use_semantic_analysis', True):
            semantic_result = self.semantic_analyzer.classify(features)
            if semantic_result:
                results.append(semantic_result)
        
        # 4. 用户画像分析
        if self.config.get('ai_settings', {}).get('use_user_profiling', True):
            user_result = self.user_profiler.classify(features)
            if user_result:
                results.append(user_result)
        
        # 5. LLM 分类（可选，需配置启用且设置 API Key）
        if self.llm_classifier and self.llm_classifier.enabled():
            llm_result = self.llm_classifier.classify(
                url,
                title,
                context={
                    'domain': features.domain,
                    'content_type': features.content_type,
                    'language': features.language
                }
            )
            if llm_result:
                results.append(llm_result)
        
        # 融合多个分类结果
        final_result = self._ensemble_classification(results, features)
        
        # 记录最终使用的分类方法
        final_method = final_result.method
        if 'rule_engine' in final_method:
            self.stats['rule_engine'] += 1
        if 'machine_learning' in final_method: # 修正: 使用 'machine_learning'
            self.stats['ml_classifier'] += 1
        if 'semantic_analyzer' in final_method:
            self.stats['semantic_analyzer'] += 1
        if 'user_profiler' in final_method:
            self.stats['user_profiler'] += 1
        if 'llm' in final_method:
            self.stats['llm'] += 1
        if final_method == 'fallback':
            self.stats['fallback'] += 1
        
        # 记录处理时间
        final_result.processing_time = (datetime.now() - start_time).total_seconds()
        
        # 更新统计
        self._update_stats(final_result)
        
        # 缓存结果
        self._cache_result(cache_key, final_result)
        
        return final_result
    
    def _cache_result(self, cache_key: str, result: ClassificationResult):
        """缓存分类结果"""
        if len(self.classification_cache) >= self._max_cache_size:
            # 简单的LRU策略：移除第一个（最旧的）缓存项
            oldest_key = next(iter(self.classification_cache))
            del self.classification_cache[oldest_key]
        
        self.classification_cache[cache_key] = result
    
    def _ensemble_classification(self, results: List[ClassificationResult], features: BookmarkFeatures) -> ClassificationResult:
        """集成多个分类结果"""
        if not results:
            return ClassificationResult(
                category="未分类",
                confidence=0.0,
                reasoning=["没有找到合适的分类方法"],
                method="fallback"
            )
        
        # 加权投票
        category_scores = defaultdict(float)
        all_reasoning = []
        methods_used = []
        
        # 权重配置
        method_weights = {
            'rule_engine': 0.35,
            'machine_learning': 0.25, # 修正: 使用 'machine_learning'
            'semantic_analyzer': 0.15,
            'user_profiler': 0.1,
            'llm': 0.5
        }
        
        for result in results:
            if isinstance(result, dict):
                # 处理字典类型的结果
                method = result.get('method', 'unknown')
                category = result.get('category', '未分类')
                confidence = result.get('confidence', 0.0)
                reasoning = result.get('reasoning', [])
            else:
                # 处理ClassificationResult对象
                method = result.method
                category = result.category
                confidence = result.confidence
                reasoning = result.reasoning
            
            weight = method_weights.get(method, 0.1)
            category_scores[category] += confidence * weight
            all_reasoning.extend(reasoning)
            methods_used.append(method)
        
        # 选择最佳分类
        if not category_scores:
            return ClassificationResult(
                category="未分类",
                confidence=0.0,
                reasoning=["所有分类方法都失败"],
                method="error"
            )
        
        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category]
        
        # 归一化置信度
        total_score = sum(category_scores.values())
        if total_score > 0:
            confidence = confidence / total_score
        
        # 生成备选分类
        alternatives = [(cat, score/total_score) for cat, score in category_scores.items() 
                       if cat != best_category]
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        # 检查层次分类
        subcategory = self._determine_subcategory(best_category, features)
        
        return ClassificationResult(
            category=best_category,
            subcategory=subcategory,
            confidence=confidence,
            reasoning=all_reasoning,
            alternatives=alternatives[:3],
            method='+'.join(set(methods_used))
        )
    
    def _determine_subcategory(self, category: str, features: BookmarkFeatures) -> Optional[str]:
        """确定子分类"""
        hierarchy = self.config.get('category_hierarchy', {})
        
        if category in hierarchy:
            subcategories = hierarchy[category]
            
            # 简单的子分类逻辑
            title_lower = features.title.lower()
            for subcat in subcategories:
                if subcat.lower() in title_lower:
                    return subcat
        
        return None
    
    def _detect_content_type(self, url: str, title: str) -> str:
        """检测内容类型"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # 视频内容
        if any(domain in url_lower for domain in ['youtube.com', 'bilibili.com', 'vimeo.com']):
            return 'video'
        
        # 代码仓库
        if any(domain in url_lower for domain in ['github.com', 'gitlab.com']):
            return 'code_repository'
        
        # 文档
        if any(pattern in url_lower for pattern in ['docs.', 'documentation', 'wiki']):
            return 'documentation'
        
        # 论文
        if any(domain in url_lower for domain in ['arxiv.org', 'acm.org', 'ieee.org']):
            return 'academic_paper'
        
        # 新闻
        if any(keyword in title_lower for keyword in ['news', '新闻', 'breaking']):
            return 'news'
        
        # 工具
        if any(keyword in title_lower for keyword in ['tool', '工具', 'online', 'generator']):
            return 'online_tool'
        
        return 'webpage'
    
    def _detect_language(self, title: str) -> str:
        """检测语言"""
        if re.search(r'[\u4e00-\u9fff]', title):
            return 'zh'
        elif re.search(r'[a-zA-Z]', title):
            return 'en'
        else:
            return 'unknown'
    
    def _update_stats(self, result: ClassificationResult):
        """更新统计信息"""
        self.stats['total_classified'] += 1
        
        # 更新平均置信度
        total = self.stats['total_classified']
        old_avg = self.stats['average_confidence']
        self.stats['average_confidence'] = (old_avg * (total - 1) + result.confidence) / total
    
    def learn_from_feedback(self, url: str, title: str, correct_category: str, predicted_category: str):
        """从用户反馈中学习"""
        features = self.extract_features(url, title)
        
        # 更新用户画像
        self.user_profiler.update_preferences(features, correct_category)
        
        # 更新机器学习模型
        if self.ml_classifier:
            self.ml_classifier.online_learn(features, correct_category)
        
        # 清除相关缓存
        cache_key = hashlib.md5(f"{url}::{title}".encode()).hexdigest()
        if cache_key in self.classification_cache:
            del self.classification_cache[cache_key]
        
        self.logger.debug(f"学习反馈: {predicted_category} -> {correct_category}")
    
    def get_statistics(self) -> Dict:
        """获取分类统计"""
        total_predictions = self.stats['rule_engine'] + self.stats['ml_classifier'] + \
                            self.stats['semantic_analyzer'] + self.stats['user_profiler'] + \
                            self.stats['llm'] + self.stats['fallback']
        
        return {
            'total_classified': self.stats['total_classified'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': self.stats['cache_hits'] / max(self.stats['total_classified'], 1),
            'average_confidence': self.stats['average_confidence'],
            'classification_methods': {
                'rule_engine': self.stats['rule_engine'],
                'ml_classifier': self.stats['ml_classifier'],
                'semantic_analyzer': self.stats['semantic_analyzer'],
                'user_profiler': self.stats['user_profiler'],
                'llm': self.stats['llm'],
                'unclassified (fallback)': self.stats['fallback'],
                'total': total_predictions
            },
            'ml_enabled': self.ml_classifier is not None
        }
    
    def save_model(self, path: str = "models/ai_classifier.json"):
        """保存模型状态"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'user_profile': self.user_profiler.export_profile(),
            'config': self.config
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, ensure_ascii=False, indent=2)
        
        # 保存ML模型
        if self.ml_classifier:
            self.ml_classifier.save_model()
        
        self.logger.info(f"模型已保存到: {path}")
    
    def load_model(self, path: str = "models/ai_classifier.json"):
        """加载模型状态"""
        if not os.path.exists(path):
            self.logger.warning(f"模型文件不存在: {path}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            self.stats = model_data.get('stats', self.stats)
            self.user_profiler.import_profile(model_data.get('user_profile', {}))
            
            # 加载ML模型
            if self.ml_classifier:
                self.ml_classifier.load_model()
            
            self.logger.info(f"模型已从 {path} 加载")
            
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")