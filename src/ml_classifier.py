"""
Advanced Machine Learning Classification System
增强机器学习分类系统

特点：
1. 多种ML算法支持（SVM, Random Forest, Naive Bayes等）
2. 自动特征工程和选择
3. 在线学习能力
4. 模型集成
5. 自动超参数优化
"""

import os
import sys
import pickle
import json
import warnings
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging
from dataclasses import dataclass
from collections import defaultdict, Counter
import hashlib
import re

# 机器学习相关导入
try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
    from sklearn.svm import SVC
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.linear_model import LogisticRegression, SGDClassifier
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.base import BaseEstimator, TransformerMixin
    from sklearn.exceptions import InconsistentVersionWarning
    import joblib
    
    # 中文分词
    import jieba
    jieba.setLogLevel(logging.WARNING)
    
    # 语言检测
    from langdetect import detect, LangDetectException
    
    ML_AVAILABLE = True
except ImportError as e:
    ML_AVAILABLE = False
    InconsistentVersionWarning = None
    print(f"警告: 机器学习依赖未安装: {e}")
    print("请运行: pip install scikit-learn jieba langdetect")

_SKLEARN_MODEL_WARNING_EMITTED = False

@dataclass
class MLFeatures:
    """机器学习特征"""
    # 文本特征
    title_tfidf: np.ndarray = None
    domain_features: np.ndarray = None
    url_features: np.ndarray = None
    
    # 数值特征
    url_length: float = 0.0
    title_length: float = 0.0
    domain_depth: float = 0.0
    path_depth: float = 0.0
    has_https: float = 0.0
    has_numbers: float = 0.0
    has_chinese: float = 0.0
    
    # 分类特征编码
    content_type_encoded: float = 0.0
    language_encoded: float = 0.0
    
    def to_array(self) -> np.ndarray:
        """转换为数组格式"""
        numerical_features = np.array([
            self.url_length, self.title_length, self.domain_depth,
            self.path_depth, self.has_https, self.has_numbers,
            self.has_chinese, self.content_type_encoded, self.language_encoded
        ])
        
        # 合并文本特征和数值特征
        if self.title_tfidf is not None:
            return np.concatenate([numerical_features, self.title_tfidf.flatten()])
        return numerical_features

class BookmarkFeatureExtractor(BaseEstimator, TransformerMixin):
    """书签特征提取器"""
    
    def __init__(self, max_features=1000, use_chinese=True):
        self.max_features = max_features
        self.use_chinese = use_chinese
        
        # 文本向量化器 - 修复空词汇表问题
        self.title_vectorizer = TfidfVectorizer(
            max_features=max_features//2,
            stop_words=None,  # 不使用停用词过滤
            ngram_range=(1, 2),
            lowercase=True,
            min_df=1,  # 最小文档频率为1
            token_pattern=r'\b\w+\b'  # 更宽松的token模式
        )
        
        self.domain_vectorizer = CountVectorizer(
            max_features=max_features//4,
            lowercase=True,
            min_df=1,  # 最小文档频率为1
            token_pattern=r'\b\w+\b'
        )
        
        self.url_vectorizer = TfidfVectorizer(
            max_features=max_features//4,
            analyzer='char_wb',
            ngram_range=(3, 5),
            lowercase=True,
            min_df=1  # 最小文档频率为1
        )
        
        # 编码器
        self.content_type_encoder = LabelEncoder()
        self.language_encoder = LabelEncoder()
        
        # 中文分词器
        if self.use_chinese:
            jieba.initialize()
        
        self.fitted = False
    
    def _chinese_tokenizer(self, text):
        """中文分词"""
        if not self.use_chinese:
            return text.split()
        
        # 检测是否包含中文
        if re.search(r'[\u4e00-\u9fff]', text):
            return list(jieba.cut(text))
        else:
            return text.split()
    
    def _extract_numerical_features(self, bookmarks):
        """提取数值特征"""
        features = []
        
        for bookmark in bookmarks:
            url = bookmark.get('url', '')
            title = bookmark.get('title', '')
            domain = bookmark.get('domain', '')
            path_segments = bookmark.get('path_segments', [])
            content_type = bookmark.get('content_type', 'unknown')
            language = bookmark.get('language', 'unknown')
            
            # 基础数值特征
            url_length = len(url) / 100.0  # 归一化
            title_length = len(title) / 50.0  # 归一化
            domain_depth = len(domain.split('.'))
            path_depth = len(path_segments)
            has_https = 1.0 if url.startswith('https') else 0.0
            has_numbers = 1.0 if re.search(r'\d', title) else 0.0
            has_chinese = 1.0 if re.search(r'[\u4e00-\u9fff]', title) else 0.0
            
            features.append([
                url_length, title_length, domain_depth, path_depth,
                has_https, has_numbers, has_chinese
            ])
        
        return np.array(features)
    
    def fit(self, bookmarks, y=None):
        """训练特征提取器"""
        titles = [bookmark.get('title', '') for bookmark in bookmarks]
        domains = [bookmark.get('domain', '') for bookmark in bookmarks]
        urls = [bookmark.get('url', '') for bookmark in bookmarks]
        content_types = [bookmark.get('content_type', 'unknown') for bookmark in bookmarks]
        languages = [bookmark.get('language', 'unknown') for bookmark in bookmarks]
        
        # 训练文本向量化器
        self.title_vectorizer.fit(titles)
        self.domain_vectorizer.fit(domains)
        self.url_vectorizer.fit(urls)
        
        # 训练编码器
        self.content_type_encoder.fit(content_types)
        self.language_encoder.fit(languages)
        
        self.fitted = True
        return self
    
    def transform(self, bookmarks):
        """转换特征"""
        if not self.fitted:
            raise ValueError("特征提取器尚未训练，请先调用 fit()")
        
        titles = [bookmark.get('title', '') for bookmark in bookmarks]
        domains = [bookmark.get('domain', '') for bookmark in bookmarks]
        urls = [bookmark.get('url', '') for bookmark in bookmarks]
        content_types = [bookmark.get('content_type', 'unknown') for bookmark in bookmarks]
        languages = [bookmark.get('language', 'unknown') for bookmark in bookmarks]
        
        # 文本特征
        title_features = self.title_vectorizer.transform(titles).toarray()
        domain_features = self.domain_vectorizer.transform(domains).toarray()
        url_features = self.url_vectorizer.transform(urls).toarray()
        
        # 数值特征
        numerical_features = self._extract_numerical_features(bookmarks)
        
        # 分类特征编码 - 增加对未见标签的处理
        def safe_transform(encoder, values):
            """安全地转换标签，处理未见过的标签"""
            transformed = []
            for v in values:
                try:
                    # 尝试转换，如果失败则视为 "未知"
                    transformed.append(encoder.transform([v])[0])
                except ValueError:
                    # 如果是未见过的标签，则查找 "unknown" 的编码值
                    try:
                        unknown_class = encoder.transform(['unknown'])[0]
                        transformed.append(unknown_class)
                    except ValueError:
                        # 如果连 "unknown" 都没有，则使用0作为默认值
                        transformed.append(0)
            return np.array(transformed).reshape(-1, 1)

        content_type_encoded = safe_transform(self.content_type_encoder, content_types)
        language_encoded = safe_transform(self.language_encoder, languages)
        
        # 合并所有特征
        all_features = np.hstack([
            numerical_features,
            title_features,
            domain_features,
            url_features,
            content_type_encoded,
            language_encoded
        ])
        
        return all_features

class MLBookmarkClassifier:
    """机器学习书签分类器"""
    
    def __init__(self, model_dir="models/ml", use_ensemble=True):
        self.model_dir = model_dir
        self.use_ensemble = use_ensemble
        
        # 创建模型目录
        os.makedirs(model_dir, exist_ok=True)
        
        # 特征提取器
        self.feature_extractor = None
        
        # 分类模型
        self.models = {}
        self.ensemble_model = None
        self.label_encoder = LabelEncoder()
        
        # 训练数据和标签
        self.training_data = []
        self.training_labels = []
        
        # 统计信息
        self.training_stats = {
            'total_samples': 0,
            'categories_count': 0,
            'accuracy_scores': {},
            'last_training_time': None
        }
        
        # 在线学习缓冲区
        self.online_buffer = {'data': [], 'labels': []}
        self.online_buffer_size = 1000
        
        self.logger = logging.getLogger(__name__)
    
    def _create_models(self):
        """创建机器学习模型"""
        models = {}
        
        # 1. Random Forest
        models['rf'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # 2. SVM
        models['svm'] = SVC(
            kernel='rbf',
            probability=True,
            random_state=42
        )
        
        # 3. Logistic Regression
        models['lr'] = LogisticRegression(
            max_iter=1000,
            random_state=42
        )
        
        # 4. Naive Bayes
        models['nb'] = MultinomialNB(alpha=0.1)
        
        # 5. Gradient Boosting
        models['gb'] = GradientBoostingClassifier(
            n_estimators=100,
            random_state=42
        )
        
        # 6. SGD (用于在线学习)
        models['sgd'] = SGDClassifier(
            loss='log_loss',
            random_state=42
        )
        
        if self.use_ensemble:
            # 集成模型
            ensemble_models = [
                ('rf', models['rf']),
                ('lr', models['lr']),
                ('nb', models['nb'])
            ]
            
            models['ensemble'] = VotingClassifier(
                estimators=ensemble_models,
                voting='soft'
            )
        
        return models
    
    def add_training_data(self, bookmarks: List[Dict], categories: List[str]):
        """添加训练数据"""
        if not ML_AVAILABLE:
            self.logger.warning("机器学习依赖不可用")
            return
        
        self.training_data.extend(bookmarks)
        self.training_labels.extend(categories)
        
        self.logger.debug(f"添加了 {len(bookmarks)} 个训练样本")
    
    def train(self, validation_split=0.2, optimize_hyperparams=False):
        """训练模型"""
        if not ML_AVAILABLE:
            self.logger.warning("机器学习依赖不可用，跳过训练")
            return False
        
        if len(self.training_data) < 10:
            self.logger.warning("训练数据不足，需要至少10个样本")
            return False
        
        self.logger.info(f"开始训练，共 {len(self.training_data)} 个样本")
        
        try:
            # 初始化特征提取器
            self.feature_extractor = BookmarkFeatureExtractor()
            
            # 提取特征
            X = self.feature_extractor.fit_transform(self.training_data)

            # 处理样本数过少的分类，将其合并
            min_samples_threshold = 2
            label_counts = Counter(self.training_labels)
            
            small_categories = {label for label, count in label_counts.items() if count < min_samples_threshold}
            
            processed_labels = list(self.training_labels)
            if small_categories:
                self.logger.warning(
                    f"发现 {len(small_categories)} 个类别的样本数少于 {min_samples_threshold}。"
                    f"将把它们合并到 '_MERGED_CATEGORY_' 中: {', '.join(small_categories)}"
                )
                
                # 用一个统一的分类来替换小分类
                processed_labels = ['_MERGED_CATEGORY_' if label in small_categories else label for label in processed_labels]

            # 编码标签
            y = self.label_encoder.fit_transform(processed_labels)
            
            # 检查合并后是否仍有问题
            unique_classes, class_counts = np.unique(y, return_counts=True)
            min_samples_in_class = class_counts.min() if len(class_counts) > 0 else 0
            
            stratify_param = y
            if min_samples_in_class < 2:
                self.logger.warning(
                    "合并后仍然存在样本数少于2的类别，无法进行分层抽样。"
                    "将禁用分层来分割训练/验证集。"
                )
                stratify_param = None

            # 划分训练集和验证集
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=validation_split, random_state=42, stratify=stratify_param
            )
            
            # 创建模型
            self.models = self._create_models()
            
            # 训练所有模型
            for name, model in self.models.items():
                self.logger.info(f"训练模型: {name}")
                
                if optimize_hyperparams and name == 'rf':
                    # 超参数优化（仅对Random Forest）
                    param_grid = {
                        'n_estimators': [50, 100, 200],
                        'max_depth': [5, 10, 15, None],
                        'min_samples_split': [2, 5, 10]
                    }
                    
                    # 动态调整CV折数以避免小类别错误
                    from sklearn.model_selection import StratifiedKFold
                    
                    n_splits_default = 3
                    min_samples = np.min(np.bincount(y_train))
                    
                    # 交叉验证折数不能超过最小类别的样本数
                    cv_splits = n_splits_default
                    if min_samples < n_splits_default:
                        cv_splits = max(2, min_samples)
                        self.logger.warning(
                            f"最小类别的样本数 ({min_samples}) 少于默认的CV折数 ({n_splits_default})。"
                            f"自动将CV折数调整为 {cv_splits}。"
                        )

                    if cv_splits >= 2:
                        cv_strategy = StratifiedKFold(n_splits=cv_splits)
                        grid_search = GridSearchCV(
                            model, param_grid, cv=cv_strategy, scoring='accuracy', n_jobs=-1
                        )
                        grid_search.fit(X_train, y_train)
                        model = grid_search.best_estimator_
                        self.models[name] = model
                        self.logger.info(f"最佳参数: {grid_search.best_params_}")
                    else:
                        self.logger.warning("由于类别样本数过少 (少于2)，跳过超参数优化。")
                
                # 训练模型
                model.fit(X_train, y_train)
                
                # 验证模型
                if len(X_val) > 0:
                    y_pred = model.predict(X_val)
                    accuracy = accuracy_score(y_val, y_pred)
                    self.training_stats['accuracy_scores'][name] = accuracy
                    self.logger.info(f"{name} 验证准确率: {accuracy:.3f}")
            
            # 选择最佳模型作为集成模型
            if self.use_ensemble and 'ensemble' in self.models:
                self.ensemble_model = self.models['ensemble']
            else:
                # 选择准确率最高的模型
                best_model_name = max(
                    self.training_stats['accuracy_scores'].items(),
                    key=lambda x: x[1]
                )[0]
                self.ensemble_model = self.models[best_model_name]
                self.logger.info(f"选择最佳模型: {best_model_name}")
            
            # 更新统计信息
            self.training_stats.update({
                'total_samples': len(self.training_data),
                'categories_count': len(set(self.training_labels)),
                'last_training_time': datetime.now().isoformat(),
                'python_version': sys.version.split()[0],
                'numpy_version': np.__version__,
                'sklearn_version': getattr(sys.modules.get('sklearn'), '__version__', None)
            })
            
            self.logger.info("模型训练完成")
            return True
            
        except Exception as e:
            self.logger.error(f"模型训练失败: {e}")
            return False
    
    def predict(self, bookmarks: List[Dict]) -> List[Tuple[str, float]]:
        """预测分类"""
        if not ML_AVAILABLE or self.ensemble_model is None:
            return [("未分类", 0.0)] * len(bookmarks)
        
        try:
            # 提取特征
            X = self.feature_extractor.transform(bookmarks)
            
            # 预测
            if hasattr(self.ensemble_model, 'predict_proba'):
                proba = self.ensemble_model.predict_proba(X)
                predictions = self.ensemble_model.predict(X)
                
                results = []
                for i, pred in enumerate(predictions):
                    category = self.label_encoder.inverse_transform([pred])[0]
                    confidence = np.max(proba[i])
                    results.append((category, confidence))
                
                return results
            else:
                predictions = self.ensemble_model.predict(X)
                categories = self.label_encoder.inverse_transform(predictions)
                return [(cat, 0.7) for cat in categories]  # 默认置信度
                
        except Exception as e:
            self.logger.error(f"预测失败: {e}")
            return [("未分类", 0.0)] * len(bookmarks)
    
    def predict_single(self, bookmark: Dict) -> Tuple[str, float]:
        """预测单个书签"""
        results = self.predict([bookmark])
        return results[0] if results else ("未分类", 0.0)
    
    def online_learn(self, bookmark: Dict, correct_category: str):
        """在线学习"""
        if not ML_AVAILABLE:
            return
        
        # 添加到缓冲区
        self.online_buffer['data'].append(bookmark)
        self.online_buffer['labels'].append(correct_category)
        
        # 如果缓冲区满了，进行增量训练
        if len(self.online_buffer['data']) >= self.online_buffer_size:
            self._incremental_train()
    
    def _incremental_train(self):
        """增量训练"""
        if not self.online_buffer['data'] or 'sgd' not in self.models:
            return
        
        try:
            # 提取特征
            X = self.feature_extractor.transform(self.online_buffer['data'])
            
            # 编码标签
            y = []
            for label in self.online_buffer['labels']:
                if label in self.label_encoder.classes_:
                    y.append(self.label_encoder.transform([label])[0])
                else:
                    # 新类别，暂时跳过
                    continue
            
            if len(y) > 0:
                # 增量训练SGD模型
                self.models['sgd'].partial_fit(X[:len(y)], y)
                self.logger.info(f"增量训练完成，{len(y)} 个样本")
            
            # 清空缓冲区
            self.online_buffer = {'data': [], 'labels': []}
            
        except Exception as e:
            self.logger.error(f"增量训练失败: {e}")
    
    def get_feature_importance(self, top_n=20) -> Dict[str, float]:
        """获取特征重要性"""
        if not ML_AVAILABLE or 'rf' not in self.models:
            return {}
        
        try:
            rf_model = self.models['rf']
            if hasattr(rf_model, 'feature_importances_'):
                importance = rf_model.feature_importances_
                
                # 获取特征名称（简化版）
                feature_names = [f"feature_{i}" for i in range(len(importance))]
                
                # 排序并返回前N个
                feature_importance = dict(zip(feature_names, importance))
                sorted_features = sorted(
                    feature_importance.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                return dict(sorted_features[:top_n])
        
        except Exception as e:
            self.logger.error(f"获取特征重要性失败: {e}")
        
        return {}
    
    def evaluate_model(self, test_bookmarks: List[Dict], test_labels: List[str]) -> Dict:
        """评估模型性能"""
        if not ML_AVAILABLE or self.ensemble_model is None:
            return {}
        
        try:
            # 预测
            predictions = [self.predict_single(bookmark)[0] for bookmark in test_bookmarks]
            
            # 计算指标
            accuracy = accuracy_score(test_labels, predictions)
            
            # 分类报告
            report = classification_report(
                test_labels, predictions, 
                output_dict=True, zero_division=0
            )
            
            return {
                'accuracy': accuracy,
                'classification_report': report,
                'confusion_matrix': confusion_matrix(test_labels, predictions).tolist()
            }
            
        except Exception as e:
            self.logger.error(f"模型评估失败: {e}")
            return {}
    
    def save_model(self):
        """保存模型"""
        if not ML_AVAILABLE:
            return
        
        try:
            # 保存特征提取器
            if self.feature_extractor:
                joblib.dump(
                    self.feature_extractor, 
                    os.path.join(self.model_dir, 'feature_extractor.pkl')
                )
            
            # 保存模型
            for name, model in self.models.items():
                joblib.dump(
                    model, 
                    os.path.join(self.model_dir, f'{name}_model.pkl')
                )
            
            # 保存标签编码器
            joblib.dump(
                self.label_encoder,
                os.path.join(self.model_dir, 'label_encoder.pkl')
            )
            
            # 保存统计信息
            with open(os.path.join(self.model_dir, 'training_stats.json'), 'w', encoding='utf-8') as f:
                json.dump(self.training_stats, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"模型已保存到: {self.model_dir}")
            
        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
    
    def load_model(self):
        """加载模型"""
        if not ML_AVAILABLE:
            return False
        
        try:
            stats_path = os.path.join(self.model_dir, 'training_stats.json')
            if os.path.exists(stats_path):
                with open(stats_path, 'r', encoding='utf-8') as f:
                    self.training_stats = json.load(f)

            captured_inconsistent_warnings = []
            with warnings.catch_warnings(record=True) as captured:
                if InconsistentVersionWarning is not None:
                    warnings.simplefilter('always', InconsistentVersionWarning)

                # 加载特征提取器
                extractor_path = os.path.join(self.model_dir, 'feature_extractor.pkl')
                if os.path.exists(extractor_path):
                    self.feature_extractor = joblib.load(extractor_path)
                
                # 加载模型
                model_files = [
                    'rf_model.pkl', 'svm_model.pkl', 'lr_model.pkl', 
                    'nb_model.pkl', 'gb_model.pkl', 'sgd_model.pkl'
                ]
                
                for model_file in model_files:
                    model_path = os.path.join(self.model_dir, model_file)
                    if os.path.exists(model_path):
                        model_name = model_file.replace('_model.pkl', '')
                        self.models[model_name] = joblib.load(model_path)
                
                # 加载集成模型
                ensemble_path = os.path.join(self.model_dir, 'ensemble_model.pkl')
                if os.path.exists(ensemble_path):
                    self.ensemble_model = joblib.load(ensemble_path)
                elif 'rf' in self.models:
                    self.ensemble_model = self.models['rf']  # 使用随机森林作为默认
                
                # 加载标签编码器
                encoder_path = os.path.join(self.model_dir, 'label_encoder.pkl')
                if os.path.exists(encoder_path):
                    self.label_encoder = joblib.load(encoder_path)

                if InconsistentVersionWarning is not None:
                    captured_inconsistent_warnings = [
                        w for w in captured if w.category is InconsistentVersionWarning
                    ]

            if captured_inconsistent_warnings:
                global _SKLEARN_MODEL_WARNING_EMITTED
                if not _SKLEARN_MODEL_WARNING_EMITTED:
                    _SKLEARN_MODEL_WARNING_EMITTED = True
                    sklearn_current = getattr(sys.modules.get('sklearn'), '__version__', None)
                    sklearn_saved = None
                    if isinstance(self.training_stats, dict):
                        sklearn_saved = self.training_stats.get('sklearn_version')
                    details = str(captured_inconsistent_warnings[0].message)
                    self.logger.warning(
                        "检测到 sklearn 版本不一致的模型反序列化警告（已汇总隐藏重复警告）。"
                        f" 当前 sklearn={sklearn_current}，模型记录 sklearn={sklearn_saved}。"
                        f" 详情示例：{details}。建议删除 models/ml 并重新训练（--train）。"
                    )
            self.logger.info(f"模型已从 {self.model_dir} 加载")
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = dict(self.training_stats)
        stats.update({
            'models_loaded': list(self.models.keys()),
            'feature_extractor_available': self.feature_extractor is not None,
            'ensemble_model_available': self.ensemble_model is not None,
            'online_buffer_size': len(self.online_buffer['data'])
        })
        return stats

# 用于集成到主分类器的包装类
class MLClassifierWrapper:
    """ML分类器包装器，用于集成到主分类系统"""
    
    def __init__(self, model_dir="models/ml"):
        self.ml_classifier = MLBookmarkClassifier(model_dir)
        self.is_trained = False
        
        # 尝试加载已有模型
        if self.ml_classifier.load_model():
            self.is_trained = True
    
    def classify(self, features, context=None) -> Optional[Dict]:
        """分类方法，返回结果字典"""
        if not self.is_trained or not ML_AVAILABLE:
            return None
        
        try:
            # 构建书签字典
            bookmark = {
                'url': features.url,
                'title': features.title,
                'domain': features.domain,
                'path_segments': features.path_segments,
                'content_type': features.content_type,
                'language': features.language
            }
            
            # 预测
            category, confidence = self.ml_classifier.predict_single(bookmark)
            
            if confidence > 0.3:  # 最低置信度阈值
                return {
                    'category': category,
                    'confidence': confidence,
                    'method': 'machine_learning'
                }
            
            return None
            
        except Exception as e:
            logging.getLogger(__name__).error(f"ML分类失败: {e}")
            return None
    
    def add_training_sample(self, features, category):
        """添加训练样本"""
        bookmark = {
            'url': features.url,
            'title': features.title,
            'domain': features.domain,
            'path_segments': features.path_segments,
            'content_type': features.content_type,
            'language': features.language
        }
        
        self.ml_classifier.add_training_data([bookmark], [category])
    
    def train_model(self):
        """训练模型"""
        if self.ml_classifier.train():
            self.is_trained = True
            self.ml_classifier.save_model()
            return True
        return False
    
    def get_stats(self):
        """获取统计信息"""
        return self.ml_classifier.get_stats()