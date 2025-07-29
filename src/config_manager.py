"""
Enhanced Configuration System
增强配置系统

特点：
1. 动态配置重载
2. 环境变量支持
3. 配置验证
4. 配置继承和覆盖
5. 实时配置监控
"""

import os
import json
import yaml
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import jsonschema
from jsonschema import validate
import copy

@dataclass
class ConfigChange:
    """配置变更记录"""
    timestamp: datetime
    path: str
    old_value: Any
    new_value: Any
    source: str = "unknown"

class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.schema = self._create_schema()
    
    def _create_schema(self) -> Dict:
        """创建配置JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "title_cleaning_rules": {
                    "type": "object",
                    "properties": {
                        "prefixes": {"type": "array", "items": {"type": "string"}},
                        "suffixes": {"type": "array", "items": {"type": "string"}},
                        "replacements": {"type": "object"}
                    }
                },
                "advanced_settings": {
                    "type": "object",
                    "properties": {
                        "classification_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                        "learning_rate": {"type": "number", "minimum": 0, "maximum": 1},
                        "max_categories": {"type": "integer", "minimum": 1},
                        "cache_size": {"type": "integer", "minimum": 100}
                    }
                },
                "category_rules": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "rules": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "match": {"type": "string", "enum": ["domain", "url", "title", "path", "content_type"]},
                                            "keywords": {"type": "array", "items": {"type": "string"}},
                                            "weight": {"type": "number", "minimum": 0},
                                            "must_not_contain": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["match", "keywords"]
                                    }
                                }
                            }
                        }
                    }
                },
                "category_order": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["category_rules"]
        }
    
    def validate(self, config: Dict) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        try:
            validate(instance=config, schema=self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"配置格式错误: {e.message} at {'.'.join(str(p) for p in e.absolute_path)}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema错误: {e.message}")
        
        # 自定义验证规则
        errors.extend(self._custom_validation(config))
        
        return errors
    
    def _custom_validation(self, config: Dict) -> List[str]:
        """自定义验证规则"""
        errors = []
        
        # 检查分类规则的逻辑性
        category_rules = config.get("category_rules", {})
        for category, rules_data in category_rules.items():
            rules = rules_data.get("rules", [])
            if not rules:
                errors.append(f"分类 '{category}' 没有定义任何规则")
            
            for i, rule in enumerate(rules):
                keywords = rule.get("keywords", [])
                if not keywords:
                    errors.append(f"分类 '{category}' 的规则 {i+1} 没有关键词")
                
                weight = rule.get("weight", 1)
                if weight < 0:
                    errors.append(f"分类 '{category}' 的规则 {i+1} 权重不能为负数")
        
        # 检查分类顺序
        category_order = config.get("category_order", [])
        defined_categories = set(category_rules.keys())
        ordered_categories = set(category_order)
        
        missing_in_order = defined_categories - ordered_categories
        if missing_in_order:
            errors.append(f"以下分类未在category_order中定义: {list(missing_in_order)}")
        
        return errors

class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path in self.config_manager.watched_files:
            self.logger.info(f"检测到配置文件变更: {event.src_path}")
            self.config_manager._reload_config(event.src_path)

class EnhancedConfigManager:
    """增强配置管理器"""
    
    def __init__(self, primary_config_path: str = "config.json"):
        self.primary_config_path = primary_config_path
        self.config = {}
        self.config_history = []
        self.change_listeners = []
        self.watched_files = set()
        
        # 文件监控
        self.observer = None
        self.file_handler = ConfigFileHandler(self)
        
        # 环境变量前缀
        self.env_prefix = "BOOKMARK_"
        
        # 配置验证器
        self.validator = ConfigValidator()
        
        # 锁
        self.config_lock = threading.RLock()
        
        self.logger = logging.getLogger(__name__)
        
        # 初始加载配置
        self._load_initial_config()
    
    def _load_initial_config(self):
        """初始加载配置"""
        try:
            self.reload_config()
            self.start_file_monitoring()
        except Exception as e:
            self.logger.error(f"初始化配置失败: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "title_cleaning_rules": {
                "prefixes": ["登录 |", "Sign in ·"],
                "suffixes": ["- V2EX", "· GitHub"],
                "replacements": {"&amp;": "&", "&lt;": "<", "&gt;": ">"}
            },
            "advanced_settings": {
                "classification_threshold": 0.6,
                "learning_rate": 0.1,
                "max_categories": 50,
                "cache_size": 10000
            },
            "category_rules": {
                "未分类": {
                    "rules": [
                        {"match": "title", "keywords": [".*"], "weight": 1}
                    ]
                }
            },
            "category_order": ["未分类"]
        }
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        with self.config_lock:
            try:
                # 加载主配置文件
                new_config = self._load_config_file(self.primary_config_path)
                
                # 应用环境变量覆盖
                new_config = self._apply_env_overrides(new_config)
                
                # 验证配置
                validation_errors = self.validator.validate(new_config)
                if validation_errors:
                    self.logger.error(f"配置验证失败: {validation_errors}")
                    return False
                
                # 保存旧配置用于比较
                old_config = copy.deepcopy(self.config)
                
                # 更新配置
                self.config = new_config
                
                # 记录变更
                self._record_changes(old_config, new_config)
                
                # 通知监听器
                self._notify_listeners(old_config, new_config)
                
                self.logger.info("配置重新加载成功")
                return True
                
            except Exception as e:
                self.logger.error(f"重新加载配置失败: {e}")
                return False
    
    def _reload_config(self, file_path: str):
        """重新加载指定文件的配置"""
        if file_path == self.primary_config_path:
            self.reload_config()
    
    def _load_config_file(self, file_path: str) -> Dict:
        """加载配置文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_ext == '.json':
                return json.load(f)
            elif file_ext in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {file_ext}")
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """应用环境变量覆盖"""
        config = copy.deepcopy(config)
        
        # 环境变量映射
        env_mappings = {
            f"{self.env_prefix}CLASSIFICATION_THRESHOLD": ("advanced_settings", "classification_threshold", float),
            f"{self.env_prefix}LEARNING_RATE": ("advanced_settings", "learning_rate", float),
            f"{self.env_prefix}MAX_CATEGORIES": ("advanced_settings", "max_categories", int),
            f"{self.env_prefix}CACHE_SIZE": ("advanced_settings", "cache_size", int),
            f"{self.env_prefix}SHOW_CONFIDENCE": ("advanced_settings", "show_confidence_indicators", bool)
        }
        
        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if section not in config:
                        config[section] = {}
                    
                    if type_func == bool:
                        config[section][key] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        config[section][key] = type_func(value)
                    
                    self.logger.info(f"环境变量覆盖: {env_var} = {config[section][key]}")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"环境变量 {env_var} 值无效: {value}, 错误: {e}")
        
        return config
    
    def _record_changes(self, old_config: Dict, new_config: Dict):
        """记录配置变更"""
        changes = self._find_changes(old_config, new_config)
        
        for change in changes:
            self.config_history.append(change)
        
        # 保持历史记录数量限制
        if len(self.config_history) > 1000:
            self.config_history = self.config_history[-1000:]
    
    def _find_changes(self, old_config: Dict, new_config: Dict, path: str = "") -> List[ConfigChange]:
        """查找配置变更"""
        changes = []
        
        # 检查新增和修改
        for key, new_value in new_config.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in old_config:
                # 新增
                changes.append(ConfigChange(
                    timestamp=datetime.now(),
                    path=current_path,
                    old_value=None,
                    new_value=new_value,
                    source="config_reload"
                ))
            elif old_config[key] != new_value:
                if isinstance(new_value, dict) and isinstance(old_config[key], dict):
                    # 递归检查嵌套字典
                    changes.extend(self._find_changes(old_config[key], new_value, current_path))
                else:
                    # 修改
                    changes.append(ConfigChange(
                        timestamp=datetime.now(),
                        path=current_path,
                        old_value=old_config[key],
                        new_value=new_value,
                        source="config_reload"
                    ))
        
        # 检查删除
        for key, old_value in old_config.items():
            if key not in new_config:
                current_path = f"{path}.{key}" if path else key
                changes.append(ConfigChange(
                    timestamp=datetime.now(),
                    path=current_path,
                    old_value=old_value,
                    new_value=None,
                    source="config_reload"
                ))
        
        return changes
    
    def _notify_listeners(self, old_config: Dict, new_config: Dict):
        """通知配置变更监听器"""
        for listener in self.change_listeners:
            try:
                listener(old_config, new_config)
            except Exception as e:
                self.logger.error(f"配置变更监听器执行失败: {e}")
    
    def start_file_monitoring(self):
        """开始文件监控"""
        if self.observer:
            return
        
        try:
            self.observer = Observer()
            
            # 监控主配置文件目录
            config_dir = os.path.dirname(os.path.abspath(self.primary_config_path))
            self.observer.schedule(self.file_handler, config_dir, recursive=False)
            
            # 添加到监控文件列表
            self.watched_files.add(os.path.abspath(self.primary_config_path))
            
            self.observer.start()
            self.logger.info(f"开始监控配置文件: {self.primary_config_path}")
            
        except Exception as e:
            self.logger.error(f"启动文件监控失败: {e}")
    
    def stop_file_monitoring(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.info("配置文件监控已停止")
    
    def add_change_listener(self, listener: Callable[[Dict, Dict], None]):
        """添加配置变更监听器"""
        self.change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[Dict, Dict], None]):
        """移除配置变更监听器"""
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
    
    def get(self, path: str, default=None):
        """获取配置值（支持点分路径）"""
        with self.config_lock:
            keys = path.split('.')
            current = self.config
            
            try:
                for key in keys:
                    current = current[key]
                return current
            except (KeyError, TypeError):
                return default
    
    def set(self, path: str, value: Any):
        """设置配置值（支持点分路径）"""
        with self.config_lock:
            keys = path.split('.')
            current = self.config
            
            # 导航到父级
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 记录变更
            old_value = current.get(keys[-1])
            current[keys[-1]] = value
            
            change = ConfigChange(
                timestamp=datetime.now(),
                path=path,
                old_value=old_value,
                new_value=value,
                source="manual_set"
            )
            self.config_history.append(change)
            
            # 通知监听器
            self._notify_listeners({}, self.config)
    
    def get_config(self) -> Dict:
        """获取完整配置"""
        with self.config_lock:
            return copy.deepcopy(self.config)
    
    def get_changes_since(self, timestamp: datetime) -> List[ConfigChange]:
        """获取指定时间以来的变更"""
        return [change for change in self.config_history if change.timestamp > timestamp]
    
    def export_config(self, file_path: str, format: str = "json"):
        """导出配置到文件"""
        with self.config_lock:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if format.lower() == "json":
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                elif format.lower() in ["yml", "yaml"]:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ValueError(f"不支持的导出格式: {format}")
            
            self.logger.info(f"配置已导出到: {file_path}")
    
    def validate_current_config(self) -> List[str]:
        """验证当前配置"""
        return self.validator.validate(self.config)
    
    def get_stats(self) -> Dict:
        """获取配置管理统计信息"""
        return {
            "config_size": len(str(self.config)),
            "change_count": len(self.config_history),
            "listener_count": len(self.change_listeners),
            "watched_files": list(self.watched_files),
            "last_reload": max(change.timestamp for change in self.config_history) if self.config_history else None,
            "validation_errors": len(self.validate_current_config())
        }

# 全局配置管理器实例
_global_config_manager = None

def get_config_manager(config_path: str = "config.json") -> EnhancedConfigManager:
    """获取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = EnhancedConfigManager(config_path)
    return _global_config_manager

def get_config(path: str = None, default=None):
    """获取配置值的便捷函数"""
    manager = get_config_manager()
    if path:
        return manager.get(path, default)
    else:
        return manager.get_config()

def set_config(path: str, value: Any):
    """设置配置值的便捷函数"""
    manager = get_config_manager()
    manager.set(path, value)