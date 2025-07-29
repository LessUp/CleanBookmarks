"""
Performance Optimization Module
性能优化模块

提供性能监控、分析和优化工具
"""

import os
import sys
import time
import psutil
import threading
import functools
from typing import Dict, List, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict, deque
import gc
import tracemalloc

@dataclass
class PerformanceMetrics:
    """性能指标"""
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime = field(default_factory=datetime.now)
    args_hash: str = ""
    cache_hit: bool = False

@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    memory_available: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history=1000):
        self.metrics_history = deque(maxlen=max_history)
        self.system_metrics = deque(maxlen=max_history)
        self.function_stats = defaultdict(list)
        
        # 系统监控线程
        self.monitoring = False
        self.monitor_thread = None
        
        # 内存追踪
        self.memory_tracking = False
        
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self, interval=1.0):
        """开始系统监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止系统监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("性能监控已停止")
    
    def _monitor_system(self, interval):
        """系统监控循环"""
        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # 内存使用率
                memory = psutil.virtual_memory()
                
                # 磁盘IO
                disk_io = psutil.disk_io_counters()
                disk_metrics = {
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0
                }
                
                # 网络IO
                network_io = psutil.net_io_counters()
                network_metrics = {
                    'bytes_sent': network_io.bytes_sent if network_io else 0,
                    'bytes_recv': network_io.bytes_recv if network_io else 0
                }
                
                metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_available=memory.available / (1024**3),  # GB
                    disk_io=disk_metrics,
                    network_io=network_metrics
                )
                
                self.system_metrics.append(metrics)
                
            except Exception as e:
                self.logger.error(f"系统监控错误: {e}")
            
            time.sleep(interval)
    
    def start_memory_tracking(self):
        """开始内存追踪"""
        tracemalloc.start()
        self.memory_tracking = True
        self.logger.info("内存追踪已启动")
    
    def get_memory_snapshot(self):
        """获取内存快照"""
        if not self.memory_tracking:
            return None
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        return {
            'total_size': sum(stat.size for stat in top_stats) / (1024**2),  # MB
            'top_files': [
                {
                    'filename': stat.traceback.format()[-1],
                    'size_mb': stat.size / (1024**2),
                    'count': stat.count
                }
                for stat in top_stats[:10]
            ]
        }
    
    def record_function_performance(self, metrics: PerformanceMetrics):
        """记录函数性能"""
        self.metrics_history.append(metrics)
        self.function_stats[metrics.function_name].append(metrics)
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}
        
        summary = {}
        
        # 函数性能统计
        for func_name, metrics_list in self.function_stats.items():
            if not metrics_list:
                continue
            
            execution_times = [m.execution_time for m in metrics_list]
            memory_usage = [m.memory_usage for m in metrics_list]
            cache_hits = sum(1 for m in metrics_list if m.cache_hit)
            
            summary[func_name] = {
                'call_count': len(metrics_list),
                'avg_execution_time': sum(execution_times) / len(execution_times),
                'max_execution_time': max(execution_times),
                'min_execution_time': min(execution_times),
                'avg_memory_usage': sum(memory_usage) / len(memory_usage),
                'max_memory_usage': max(memory_usage),
                'cache_hit_rate': cache_hits / len(metrics_list) if metrics_list else 0
            }
        
        # 系统性能统计
        if self.system_metrics:
            cpu_usage = [m.cpu_percent for m in self.system_metrics]
            memory_usage = [m.memory_percent for m in self.system_metrics]
            
            summary['system'] = {
                'avg_cpu_percent': sum(cpu_usage) / len(cpu_usage),
                'max_cpu_percent': max(cpu_usage),
                'avg_memory_percent': sum(memory_usage) / len(memory_usage),
                'max_memory_percent': max(memory_usage),
                'min_available_memory_gb': min(m.memory_available for m in self.system_metrics)
            }
        
        return summary
    
    def identify_bottlenecks(self) -> List[Dict]:
        """识别性能瓶颈"""
        bottlenecks = []
        summary = self.get_performance_summary()
        
        for func_name, stats in summary.items():
            if func_name == 'system':
                continue
            
            # 执行时间过长
            if stats['avg_execution_time'] > 1.0:  # 1秒
                bottlenecks.append({
                    'type': 'slow_execution',
                    'function': func_name,
                    'avg_time': stats['avg_execution_time'],
                    'severity': 'high' if stats['avg_execution_time'] > 5.0 else 'medium'
                })
            
            # 内存使用过高
            if stats['max_memory_usage'] > 100:  # 100MB
                bottlenecks.append({
                    'type': 'high_memory_usage',
                    'function': func_name,
                    'max_memory': stats['max_memory_usage'],
                    'severity': 'high' if stats['max_memory_usage'] > 500 else 'medium'
                })
            
            # 缓存命中率低
            if stats['cache_hit_rate'] < 0.5 and stats['call_count'] > 10:
                bottlenecks.append({
                    'type': 'low_cache_hit_rate',
                    'function': func_name,
                    'hit_rate': stats['cache_hit_rate'],
                    'severity': 'medium'
                })
        
        return bottlenecks
    
    def save_report(self, filepath: str):
        """保存性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_performance_summary(),
            'bottlenecks': self.identify_bottlenecks(),
            'memory_snapshot': self.get_memory_snapshot(),
            'recommendations': self._generate_recommendations()
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"性能报告已保存: {filepath}")
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        bottlenecks = self.identify_bottlenecks()
        
        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'slow_execution':
                recommendations.append(
                    f"函数 {bottleneck['function']} 执行缓慢，考虑算法优化或并行处理"
                )
            elif bottleneck['type'] == 'high_memory_usage':
                recommendations.append(
                    f"函数 {bottleneck['function']} 内存使用过高，考虑分批处理或优化数据结构"
                )
            elif bottleneck['type'] == 'low_cache_hit_rate':
                recommendations.append(
                    f"函数 {bottleneck['function']} 缓存命中率低，检查缓存策略"
                )
        
        # 系统级建议
        summary = self.get_performance_summary()
        if 'system' in summary:
            system_stats = summary['system']
            if system_stats['avg_cpu_percent'] > 80:
                recommendations.append("系统CPU使用率过高，考虑减少并行度或优化算法")
            
            if system_stats['avg_memory_percent'] > 85:
                recommendations.append("系统内存使用率过高，考虑增加内存或优化内存使用")
        
        return recommendations

# 全局性能监控器实例
_global_monitor = PerformanceMonitor()

def performance_monitor(func: Callable = None, *, enable_cache=False, cache_size=128):
    """性能监控装饰器"""
    def decorator(func):
        # 缓存
        if enable_cache:
            func = functools.lru_cache(maxsize=cache_size)(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # 获取进程内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024**2)  # MB
            
            # 计算参数哈希（用于缓存分析）
            args_str = str(args) + str(sorted(kwargs.items()))
            args_hash = str(hash(args_str))
            
            # 检查是否为缓存命中
            cache_hit = False
            if enable_cache and hasattr(func, 'cache_info'):
                cache_info_before = func.cache_info()
            
            try:
                result = func(*args, **kwargs)
                
                # 检查缓存命中
                if enable_cache and hasattr(func, 'cache_info'):
                    cache_info_after = func.cache_info()
                    cache_hit = cache_info_after.hits > cache_info_before.hits
                
                return result
                
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                # 获取内存使用
                memory_after = process.memory_info().rss / (1024**2)  # MB
                memory_usage = memory_after - memory_before
                
                # 获取CPU使用率（粗略估计）
                cpu_usage = psutil.cpu_percent(interval=0.1)
                
                # 记录性能指标
                metrics = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    args_hash=args_hash,
                    cache_hit=cache_hit
                )
                
                _global_monitor.record_function_performance(metrics)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

@contextmanager
def performance_context(name: str):
    """性能监控上下文管理器"""
    start_time = time.time()
    process = psutil.Process()
    memory_before = process.memory_info().rss / (1024**2)
    
    try:
        yield
    finally:
        end_time = time.time()
        execution_time = end_time - start_time
        memory_after = process.memory_info().rss / (1024**2)
        memory_usage = memory_after - memory_before
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        metrics = PerformanceMetrics(
            function_name=name,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage
        )
        
        _global_monitor.record_function_performance(metrics)

class MemoryOptimizer:
    """内存优化器"""
    
    @staticmethod
    def optimize_gc():
        """优化垃圾回收"""
        # 强制垃圾回收
        collected = gc.collect()
        
        # 设置垃圾回收阈值
        gc.set_threshold(700, 10, 10)
        
        return collected
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / (1024**2),
            'vms_mb': memory_info.vms / (1024**2),
            'percent': process.memory_percent()
        }
    
    @staticmethod
    def clear_caches():
        """清除缓存"""
        # 清除函数缓存
        for obj in gc.get_objects():
            if hasattr(obj, 'cache_clear'):
                try:
                    obj.cache_clear()
                except:
                    pass
        
        # 强制垃圾回收
        gc.collect()

class CacheManager:
    """高级缓存管理器"""
    
    def __init__(self, max_size=10000, ttl=3600):
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self.cache = {}
        self.access_times = {}
        self.creation_times = {}
        
    def get(self, key: str, default=None):
        """获取缓存值"""
        if key not in self.cache:
            return default
        
        # 检查TTL
        if time.time() - self.creation_times[key] > self.ttl:
            self.delete(key)
            return default
        
        # 更新访问时间
        self.access_times[key] = time.time()
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        # 如果缓存已满，清理最久未访问的项目
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        current_time = time.time()
        self.cache[key] = value
        self.access_times[key] = current_time
        self.creation_times[key] = current_time
    
    def delete(self, key: str):
        """删除缓存项"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.creation_times.pop(key, None)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        self.creation_times.clear()
    
    def _evict_lru(self):
        """清理最久未访问的项目"""
        if not self.access_times:
            return
        
        # 找到最久未访问的键
        lru_key = min(self.access_times, key=self.access_times.get)
        self.delete(lru_key)
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        current_time = time.time()
        expired_count = sum(
            1 for creation_time in self.creation_times.values()
            if current_time - creation_time > self.ttl
        )
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'expired_count': expired_count,
            'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
        }

def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return _global_monitor

def start_global_monitoring(interval=1.0):
    """启动全局性能监控"""
    _global_monitor.start_monitoring(interval)
    _global_monitor.start_memory_tracking()

def stop_global_monitoring():
    """停止全局性能监控"""
    _global_monitor.stop_monitoring()

def save_performance_report(filepath: str = None):
    """保存性能报告"""
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"reports/performance_report_{timestamp}.json"
    
    _global_monitor.save_report(filepath)