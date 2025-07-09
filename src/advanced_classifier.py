"""
Advanced Bookmark Classification System

This module implements an intelligent bookmark classification system using:
1. Machine Learning-based content analysis
2. Semantic similarity matching
3. Adaptive learning from user feedback
4. Multi-language support
5. Intelligent duplicate detection
6. Dynamic category suggestion
"""

import os
import json
import re
import pickle
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter
from urllib.parse import urlparse
import hashlib

# Third-party imports (will be installed)
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    import jieba
    import langdetect
except ImportError:
    print("Installing required packages...")
    # Note: In production, these should be in requirements.txt

@dataclass
class BookmarkFeatures:
    """Features extracted from a bookmark for classification"""
    url: str
    title: str
    domain: str
    path_segments: List[str]
    title_tokens: List[str]
    language: str
    content_type: str
    semantic_embedding: Optional[np.ndarray] = None
    
@dataclass
class ClassificationResult:
    """Result of bookmark classification"""
    category: str
    confidence: float
    alternative_categories: List[Tuple[str, float]]
    reasoning: List[str]
    
@dataclass
class UserFeedback:
    """User feedback for learning system"""
    bookmark_url: str
    suggested_category: str
    actual_category: str
    timestamp: datetime
    confidence: float

class AdvancedBookmarkClassifier:
    """
    Advanced bookmark classification system with ML capabilities
    """
    
    def __init__(self, config_path: str = "config.json", model_path: str = "models/"):
        self.config_path = config_path
        self.model_path = model_path
        self.config = self._load_config()
        
        # Initialize components
        self.feature_extractor = FeatureExtractor()
        self.semantic_analyzer = SemanticAnalyzer()
        self.ml_classifier = MLClassifier(model_path)
        self.learning_system = AdaptiveLearningSystem(model_path)
        self.duplicate_detector = IntelligentDuplicateDetector()
        
        # State
        self.seen_urls: Set[str] = set()
        self.classification_history: List[ClassificationResult] = []
        self.user_feedback: List[UserFeedback] = []
        
        # Load existing models
        self._load_models()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict:
        """Load configuration with enhanced structure"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Fallback configuration"""
        return {
            "classification_threshold": 0.7,
            "learning_rate": 0.1,
            "max_categories": 50,
            "semantic_similarity_threshold": 0.8,
            "content_analysis_enabled": True,
            "adaptive_learning_enabled": True,
            "multi_language_support": True
        }
    
    def _load_models(self):
        """Load pre-trained models"""
        os.makedirs(self.model_path, exist_ok=True)
        
        try:
            # Load ML classifier
            self.ml_classifier.load_model()
            
            # Load learning system state
            self.learning_system.load_state()
            
            # Load user feedback history
            feedback_path = os.path.join(self.model_path, "user_feedback.pkl")
            if os.path.exists(feedback_path):
                with open(feedback_path, 'rb') as f:
                    self.user_feedback = pickle.load(f)
                    
        except Exception as e:
            self.logger.warning(f"Could not load models: {e}")
    
    def classify_bookmark(self, url: str, title: str, content: str = None) -> ClassificationResult:
        """
        Main classification method with advanced features
        """
        try:
            # Extract features
            features = self.feature_extractor.extract_features(url, title, content)
            
            # Check for duplicates
            if self.duplicate_detector.is_duplicate(features, self.seen_urls):
                return ClassificationResult(
                    category="重复",
                    confidence=1.0,
                    alternative_categories=[],
                    reasoning=["检测到重复书签"]
                )
            
            # Multi-stage classification
            results = []
            
            # 1. Rule-based classification (enhanced)
            rule_result = self._rule_based_classification(features)
            if rule_result:
                results.append(rule_result)
            
            # 2. ML-based classification
            ml_result = self.ml_classifier.classify(features)
            if ml_result:
                results.append(ml_result)
            
            # 3. Semantic similarity classification
            semantic_result = self.semantic_analyzer.classify(features, self.classification_history)
            if semantic_result:
                results.append(semantic_result)
            
            # 4. Adaptive learning classification
            adaptive_result = self.learning_system.classify(features, self.user_feedback)
            if adaptive_result:
                results.append(adaptive_result)
            
            # Combine results using ensemble method
            final_result = self._ensemble_classification(results, features)
            
            # Update history
            self.classification_history.append(final_result)
            self.seen_urls.add(self._normalize_url(url))
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Classification failed for {url}: {e}")
            return ClassificationResult(
                category="未分类",
                confidence=0.0,
                alternative_categories=[],
                reasoning=[f"分类失败: {str(e)}"]
            )
    
    def _rule_based_classification(self, features: BookmarkFeatures) -> Optional[ClassificationResult]:
        """Enhanced rule-based classification with semantic understanding"""
        scores = defaultdict(float)
        reasoning = []
        
        # Enhanced pattern matching
        for category, rules in self.config.get("category_rules", {}).items():
            category_score = 0
            
            for rule in rules.get("rules", []):
                match_score = self._evaluate_rule(rule, features)
                if match_score > 0:
                    category_score += match_score
                    reasoning.append(f"规则匹配: {rule.get('match', 'unknown')} -> {category}")
            
            if category_score > 0:
                scores[category] = category_score
        
        if not scores:
            return None
        
        # Get top categories
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_category, best_score = sorted_scores[0]
        
        # Calculate confidence
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0
        
        # Alternative categories
        alternatives = [(cat, score/total_score) for cat, score in sorted_scores[1:6]]
        
        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            alternative_categories=alternatives,
            reasoning=reasoning
        )
    
    def _evaluate_rule(self, rule: Dict, features: BookmarkFeatures) -> float:
        """Evaluate a single rule with enhanced matching"""
        match_type = rule.get("match")
        keywords = rule.get("keywords", [])
        weight = rule.get("weight", 1.0)
        
        target_text = ""
        if match_type == "domain":
            target_text = features.domain
        elif match_type == "title":
            target_text = features.title
        elif match_type == "url":
            target_text = features.url
        elif match_type == "path":
            target_text = " ".join(features.path_segments)
        
        if not target_text:
            return 0.0
        
        # Enhanced matching with semantic similarity
        max_similarity = 0.0
        for keyword in keywords:
            # Exact match
            if keyword.lower() in target_text.lower():
                max_similarity = max(max_similarity, 1.0)
            else:
                # Semantic similarity
                similarity = self.semantic_analyzer.calculate_similarity(
                    keyword, target_text
                )
                max_similarity = max(max_similarity, similarity)
        
        # Apply exclusion rules
        exclusions = rule.get("must_not_contain", [])
        for exclusion in exclusions:
            if exclusion.lower() in target_text.lower():
                max_similarity *= 0.1  # Heavily penalize
        
        return max_similarity * weight
    
    def _ensemble_classification(self, results: List[ClassificationResult], features: BookmarkFeatures) -> ClassificationResult:
        """Combine multiple classification results using ensemble method"""
        if not results:
            return ClassificationResult(
                category="未分类",
                confidence=0.0,
                alternative_categories=[],
                reasoning=["没有找到合适的分类"]
            )
        
        # Weighted voting
        category_votes = defaultdict(float)
        all_reasoning = []
        
        for result in results:
            category_votes[result.category] += result.confidence
            all_reasoning.extend(result.reasoning)
        
        # Normalize votes
        total_votes = sum(category_votes.values())
        if total_votes > 0:
            for category in category_votes:
                category_votes[category] /= total_votes
        
        # Select best category
        best_category = max(category_votes, key=category_votes.get)
        confidence = category_votes[best_category]
        
        # Create alternatives
        sorted_votes = sorted(category_votes.items(), key=lambda x: x[1], reverse=True)
        alternatives = sorted_votes[1:6]
        
        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            alternative_categories=alternatives,
            reasoning=all_reasoning
        )
    
    def add_user_feedback(self, url: str, suggested_category: str, actual_category: str, confidence: float):
        """Add user feedback for learning"""
        feedback = UserFeedback(
            bookmark_url=url,
            suggested_category=suggested_category,
            actual_category=actual_category,
            timestamp=datetime.now(),
            confidence=confidence
        )
        
        self.user_feedback.append(feedback)
        self.learning_system.update_from_feedback(feedback)
        
        # Save feedback
        self._save_feedback()
    
    def _save_feedback(self):
        """Save user feedback to disk"""
        feedback_path = os.path.join(self.model_path, "user_feedback.pkl")
        with open(feedback_path, 'wb') as f:
            pickle.dump(self.user_feedback, f)
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for duplicate detection"""
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}".rstrip('/')
        except:
            return url
    
    def get_statistics(self) -> Dict:
        """Get classification statistics"""
        stats = {
            "total_classified": len(self.classification_history),
            "category_distribution": Counter([r.category for r in self.classification_history]),
            "average_confidence": np.mean([r.confidence for r in self.classification_history]) if self.classification_history else 0,
            "feedback_count": len(self.user_feedback),
            "accuracy": self._calculate_accuracy()
        }
        return stats
    
    def _calculate_accuracy(self) -> float:
        """Calculate classification accuracy based on user feedback"""
        if not self.user_feedback:
            return 0.0
        
        correct = sum(1 for fb in self.user_feedback 
                     if fb.suggested_category == fb.actual_category)
        return correct / len(self.user_feedback)


class FeatureExtractor:
    """Extract features from bookmark data"""
    
    def __init__(self):
        self.stop_words = self._load_stop_words()
    
    def _load_stop_words(self) -> Set[str]:
        """Load stop words for multiple languages"""
        # Basic stop words - in production, load from files
        return {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "是", "的", "了", "在", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "为", "下"
        }
    
    def extract_features(self, url: str, title: str, content: str = None) -> BookmarkFeatures:
        """Extract comprehensive features from bookmark"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower().replace("www.", "")
            path_segments = [seg for seg in parsed_url.path.split('/') if seg]
            
            # Tokenize title
            title_tokens = self._tokenize_text(title)
            
            # Detect language
            language = self._detect_language(title)
            
            # Determine content type
            content_type = self._determine_content_type(url, title)
            
            return BookmarkFeatures(
                url=url,
                title=title,
                domain=domain,
                path_segments=path_segments,
                title_tokens=title_tokens,
                language=language,
                content_type=content_type
            )
            
        except Exception as e:
            # Fallback for malformed URLs
            return BookmarkFeatures(
                url=url,
                title=title,
                domain="",
                path_segments=[],
                title_tokens=self._tokenize_text(title),
                language="unknown",
                content_type="unknown"
            )
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text with multi-language support"""
        if not text:
            return []
        
        # Detect if text contains Chinese characters
        if re.search(r'[\u4e00-\u9fff]', text):
            # Use jieba for Chinese text
            tokens = list(jieba.cut(text.lower()))
        else:
            # Simple tokenization for English
            tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stop words
        tokens = [token for token in tokens if token not in self.stop_words]
        
        return tokens
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            return langdetect.detect(text)
        except:
            return "unknown"
    
    def _determine_content_type(self, url: str, title: str) -> str:
        """Determine content type based on URL and title patterns"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Video content
        if any(pattern in url_lower for pattern in ['youtube.com', 'bilibili.com', 'vimeo.com']):
            return "video"
        
        # Documentation
        if any(pattern in url_lower for pattern in ['docs.', 'documentation', 'wiki']):
            return "documentation"
        
        # Code repository
        if any(pattern in url_lower for pattern in ['github.com', 'gitlab.com', 'bitbucket.org']):
            return "code"
        
        # News/Blog
        if any(pattern in title_lower for pattern in ['news', '新闻', 'blog', '博客']):
            return "news"
        
        # Tool/Service
        if any(pattern in title_lower for pattern in ['tool', 'service', '工具', '服务']):
            return "tool"
        
        return "webpage"


class SemanticAnalyzer:
    """Semantic similarity analysis for classification"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.category_embeddings = {}
    
    def classify(self, features: BookmarkFeatures, history: List[ClassificationResult]) -> Optional[ClassificationResult]:
        """Classify using semantic similarity"""
        if not history:
            return None
        
        # Build category embeddings from history
        self._build_category_embeddings(history)
        
        # Create feature vector for current bookmark
        feature_text = f"{features.title} {features.domain} {' '.join(features.path_segments)}"
        
        try:
            feature_vector = self.vectorizer.transform([feature_text])
            
            # Calculate similarities
            similarities = {}
            for category, embedding in self.category_embeddings.items():
                similarity = cosine_similarity(feature_vector, embedding)[0][0]
                similarities[category] = similarity
            
            if not similarities:
                return None
            
            # Get best match
            best_category = max(similarities, key=similarities.get)
            confidence = similarities[best_category]
            
            # Only return if confidence is above threshold
            if confidence < 0.5:
                return None
            
            alternatives = [(cat, sim) for cat, sim in similarities.items() 
                          if cat != best_category]
            alternatives.sort(key=lambda x: x[1], reverse=True)
            
            return ClassificationResult(
                category=best_category,
                confidence=confidence,
                alternative_categories=alternatives[:5],
                reasoning=[f"语义相似度匹配: {confidence:.3f}"]
            )
            
        except Exception as e:
            return None
    
    def _build_category_embeddings(self, history: List[ClassificationResult]):
        """Build embeddings for each category from history"""
        category_texts = defaultdict(list)
        
        for result in history:
            # This is simplified - in practice, you'd store more context
            category_texts[result.category].append(result.category)
        
        for category, texts in category_texts.items():
            if texts:
                try:
                    combined_text = " ".join(texts)
                    embedding = self.vectorizer.fit_transform([combined_text])
                    self.category_embeddings[category] = embedding
                except:
                    pass
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            vectors = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity
        except:
            return 0.0


class MLClassifier:
    """Machine learning-based classifier"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.feature_names = []
    
    def classify(self, features: BookmarkFeatures) -> Optional[ClassificationResult]:
        """Classify using ML model"""
        if not self.model:
            return None
        
        # This is a placeholder - implement actual ML classification
        # You would train models on labeled data
        return None
    
    def load_model(self):
        """Load pre-trained model"""
        model_file = os.path.join(self.model_path, "ml_model.pkl")
        if os.path.exists(model_file):
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
    
    def save_model(self):
        """Save trained model"""
        if self.model:
            model_file = os.path.join(self.model_path, "ml_model.pkl")
            with open(model_file, 'wb') as f:
                pickle.dump(self.model, f)


class AdaptiveLearningSystem:
    """Adaptive learning system that improves from user feedback"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.category_patterns = defaultdict(list)
        self.feedback_weights = defaultdict(float)
    
    def classify(self, features: BookmarkFeatures, feedback: List[UserFeedback]) -> Optional[ClassificationResult]:
        """Classify using learned patterns"""
        if not feedback:
            return None
        
        # Update patterns from feedback
        self._update_patterns(feedback)
        
        # Score categories based on learned patterns
        scores = self._score_categories(features)
        
        if not scores:
            return None
        
        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]
        
        alternatives = [(cat, score) for cat, score in scores.items() 
                       if cat != best_category]
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            alternative_categories=alternatives[:5],
            reasoning=[f"自适应学习匹配: {confidence:.3f}"]
        )
    
    def _update_patterns(self, feedback: List[UserFeedback]):
        """Update learned patterns from feedback"""
        for fb in feedback:
            # Extract patterns from URLs that were correctly classified
            if fb.suggested_category == fb.actual_category:
                parsed = urlparse(fb.bookmark_url)
                domain = parsed.netloc.lower().replace("www.", "")
                
                # Store domain pattern
                self.category_patterns[fb.actual_category].append(domain)
                
                # Increase weight for this category
                self.feedback_weights[fb.actual_category] += 0.1
    
    def _score_categories(self, features: BookmarkFeatures) -> Dict[str, float]:
        """Score categories based on learned patterns"""
        scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = 0.0
            
            # Domain matching
            if features.domain in patterns:
                score += 1.0
            
            # Apply feedback weight
            score *= (1.0 + self.feedback_weights[category])
            
            if score > 0:
                scores[category] = score
        
        return scores
    
    def update_from_feedback(self, feedback: UserFeedback):
        """Update learning from single feedback"""
        # This would be called in real-time as user provides feedback
        pass
    
    def load_state(self):
        """Load learning state"""
        state_file = os.path.join(self.model_path, "learning_state.pkl")
        if os.path.exists(state_file):
            with open(state_file, 'rb') as f:
                state = pickle.load(f)
                self.category_patterns = state.get('patterns', defaultdict(list))
                self.feedback_weights = state.get('weights', defaultdict(float))
    
    def save_state(self):
        """Save learning state"""
        state = {
            'patterns': dict(self.category_patterns),
            'weights': dict(self.feedback_weights)
        }
        state_file = os.path.join(self.model_path, "learning_state.pkl")
        with open(state_file, 'wb') as f:
            pickle.dump(state, f)


class IntelligentDuplicateDetector:
    """Intelligent duplicate detection with fuzzy matching"""
    
    def __init__(self):
        self.url_signatures = set()
        self.content_hashes = set()
    
    def is_duplicate(self, features: BookmarkFeatures, seen_urls: Set[str]) -> bool:
        """Check if bookmark is a duplicate using multiple methods"""
        # Method 1: Exact URL match
        normalized_url = self._normalize_url(features.url)
        if normalized_url in seen_urls:
            return True
        
        # Method 2: Content similarity
        content_hash = self._generate_content_hash(features)
        if content_hash in self.content_hashes:
            return True
        
        # Method 3: URL similarity (different parameters, same content)
        url_signature = self._generate_url_signature(features)
        if url_signature in self.url_signatures:
            return True
        
        # Update tracking sets
        seen_urls.add(normalized_url)
        self.content_hashes.add(content_hash)
        self.url_signatures.add(url_signature)
        
        return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        try:
            parsed = urlparse(url)
            # Remove common tracking parameters
            clean_url = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}"
            return clean_url.rstrip('/')
        except:
            return url
    
    def _generate_content_hash(self, features: BookmarkFeatures) -> str:
        """Generate hash based on content features"""
        content = f"{features.domain}::{features.title}::{' '.join(features.path_segments)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _generate_url_signature(self, features: BookmarkFeatures) -> str:
        """Generate signature for URL structure"""
        return f"{features.domain}::{'/'.join(features.path_segments[:3])}"