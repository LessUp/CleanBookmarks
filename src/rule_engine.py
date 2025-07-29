"""
Rule Engine - 基于规则的快速分类引擎

提供高效的基于规则的书签分类，作为AI分类的基础组件
"""

import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
from urllib.parse import urlparse

@dataclass
class RuleMatch:
    """规则匹配结果"""
    rule_id: str
    category: str
    confidence: float
    matched_text: str
    rule_type: str

class RuleEngine:
    """规则引擎"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 预编译规则
        self.compiled_rules = {}
        self._compile_rules()
        
        # 性能统计
        self.stats = {
            'total_matches': 0,
            'rule_hits': defaultdict(int),
            'category_predictions': defaultdict(int)
        }
    
    def _compile_rules(self):
        """预编译规则以提高性能"""
        category_rules = self.config.get('category_rules', {})
        
        for category, category_data in category_rules.items():
            rules = category_data.get('rules', [])
            
            self.compiled_rules[category] = []
            
            for i, rule in enumerate(rules):
                rule_id = f"{category}_{i}"
                match_type = rule.get('match', '')
                keywords = rule.get('keywords', [])
                weight = rule.get('weight', 1.0)
                exclusions = rule.get('must_not_contain', [])
                
                # 预编译正则表达式
                compiled_patterns = []
                for keyword in keywords:
                    try:
                        # 转义特殊字符，但保留一些通配符
                        escaped_keyword = re.escape(keyword).replace(r'\*', '.*').replace(r'\?', '.')
                        pattern = re.compile(escaped_keyword, re.IGNORECASE)
                        compiled_patterns.append(pattern)
                    except re.error:
                        self.logger.warning(f"无效的正则表达式: {keyword}")
                        continue
                
                compiled_exclusions = []
                for exclusion in exclusions:
                    try:
                        pattern = re.compile(re.escape(exclusion), re.IGNORECASE)
                        compiled_exclusions.append(pattern)
                    except re.error:
                        continue
                
                compiled_rule = {
                    'rule_id': rule_id,
                    'match_type': match_type,
                    'patterns': compiled_patterns,
                    'exclusions': compiled_exclusions,
                    'weight': weight,
                    'original_keywords': keywords
                }
                
                self.compiled_rules[category].append(compiled_rule)
        
        self.logger.info(f"预编译了 {sum(len(rules) for rules in self.compiled_rules.values())} 个规则")
    
    def classify(self, features) -> Optional[Dict]:
        """基于规则进行分类"""
        try:
            matches = self._find_matches(features)
            
            if not matches:
                return None
            
            # 计算分类得分
            category_scores = self._calculate_scores(matches)
            
            if not category_scores:
                return None
            
            # 选择最佳分类
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category]
            
            # 归一化置信度
            total_score = sum(category_scores.values())
            if total_score > 0:
                confidence = confidence / total_score
            
            # 生成推理过程
            reasoning = self._generate_reasoning(matches, best_category)
            
            # 生成备选分类
            alternatives = [(cat, score/total_score) for cat, score in category_scores.items() 
                          if cat != best_category]
            alternatives.sort(key=lambda x: x[1], reverse=True)
            
            self.stats['total_matches'] += 1
            self.stats['category_predictions'][best_category] += 1
            
            return {
                'category': best_category,
                'confidence': confidence,
                'alternatives': alternatives[:3],
                'reasoning': reasoning,
                'method': 'rule_engine'
            }
            
        except Exception as e:
            self.logger.error(f"规则分类失败: {e}")
            return None
    
    def _find_matches(self, features) -> List[RuleMatch]:
        """查找匹配的规则"""
        matches = []
        
        # 准备匹配文本
        match_texts = {
            'domain': features.domain,
            'title': features.title.lower(),
            'url': features.url.lower(),
            'path': '/'.join(features.path_segments).lower(),
            'content_type': features.content_type
        }
        
        for category, rules in self.compiled_rules.items():
            for rule in rules:
                match_type = rule['match_type']
                target_text = match_texts.get(match_type, '')
                
                if not target_text:
                    continue
                
                # 检查模式匹配
                for pattern in rule['patterns']:
                    match = pattern.search(target_text)
                    if match:
                        # 检查排除条件
                        excluded = False
                        for exclusion_pattern in rule['exclusions']:
                            if exclusion_pattern.search(target_text):
                                excluded = True
                                break
                        
                        if not excluded:
                            rule_match = RuleMatch(
                                rule_id=rule['rule_id'],
                                category=category,
                                confidence=rule['weight'],
                                matched_text=match.group(),
                                rule_type=match_type
                            )
                            matches.append(rule_match)
                            self.stats['rule_hits'][rule['rule_id']] += 1
                            break  # 每个规则只匹配一次
        
        return matches
    
    def _calculate_scores(self, matches: List[RuleMatch]) -> Dict[str, float]:
        """计算分类得分"""
        category_scores = defaultdict(float)
        
        for match in matches:
            category_scores[match.category] += match.confidence
        
        return dict(category_scores)
    
    def _generate_reasoning(self, matches: List[RuleMatch], best_category: str) -> List[str]:
        """生成推理过程"""
        reasoning = []
        
        category_matches = [m for m in matches if m.category == best_category]
        
        for match in category_matches:
            reasoning.append(
                f"规则匹配: {match.rule_type} 包含 '{match.matched_text}' -> {match.category}"
            )
        
        return reasoning
    
    def add_dynamic_rule(self, category: str, match_type: str, keyword: str, weight: float = 1.0):
        """动态添加规则"""
        if category not in self.compiled_rules:
            self.compiled_rules[category] = []
        
        rule_id = f"{category}_dynamic_{len(self.compiled_rules[category])}"
        
        try:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            
            compiled_rule = {
                'rule_id': rule_id,
                'match_type': match_type,
                'patterns': [pattern],
                'exclusions': [],
                'weight': weight,
                'original_keywords': [keyword]
            }
            
            self.compiled_rules[category].append(compiled_rule)
            self.logger.info(f"添加动态规则: {category} - {match_type}:{keyword}")
            
        except re.error as e:
            self.logger.error(f"无效的动态规则: {keyword}, 错误: {e}")
    
    def update_rule_weight(self, rule_id: str, new_weight: float):
        """更新规则权重"""
        for category, rules in self.compiled_rules.items():
            for rule in rules:
                if rule['rule_id'] == rule_id:
                    old_weight = rule['weight']
                    rule['weight'] = new_weight
                    self.logger.info(f"更新规则权重: {rule_id} {old_weight} -> {new_weight}")
                    return True
        
        self.logger.warning(f"未找到规则: {rule_id}")
        return False
    
    def get_rule_performance(self) -> Dict:
        """获取规则性能统计"""
        total_hits = sum(self.stats['rule_hits'].values())
        
        return {
            'total_matches': self.stats['total_matches'],
            'total_rule_hits': total_hits,
            'top_rules': dict(sorted(self.stats['rule_hits'].items(), 
                                   key=lambda x: x[1], reverse=True)[:10]),
            'category_distribution': dict(self.stats['category_predictions']),
            'rules_count': sum(len(rules) for rules in self.compiled_rules.values())
        }
    
    def export_rules(self) -> Dict:
        """导出规则配置"""
        exported_rules = {}
        
        for category, rules in self.compiled_rules.items():
            exported_rules[category] = []
            
            for rule in rules:
                exported_rule = {
                    'match': rule['match_type'],
                    'keywords': rule['original_keywords'],
                    'weight': rule['weight']
                }
                exported_rules[category].append(exported_rule)
        
        return {
            'category_rules': exported_rules,
            'performance_stats': self.get_rule_performance()
        }
    
    def validate_rules(self) -> List[str]:
        """验证规则配置"""
        errors = []
        
        for category, rules in self.compiled_rules.items():
            if not rules:
                errors.append(f"分类 '{category}' 没有定义规则")
                continue
            
            for rule in rules:
                if not rule['patterns']:
                    errors.append(f"分类 '{category}' 包含无效的模式")
                
                if rule['weight'] <= 0:
                    errors.append(f"分类 '{category}' 包含无效的权重: {rule['weight']}")
        
        return errors