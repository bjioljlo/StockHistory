"""
Performance Monitor Module
==========================

Performance monitoring, profiling, and metrics collection system.

Features:
- Method execution time profiling
- Cache hit/miss statistics
- Performance metrics tracking
- Thread-safe counters
- Reporting and logging integration
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, Callable
from collections import defaultdict, deque


logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Thread-safe performance metrics storage."""
    
    def __init__(self, max_history_size: int = 1000):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self._start_times: Dict[str, float] = {}
        self.max_history_size = max_history_size
    
    def increment(self, metric_name: str, value: int = 1) -> None:
        """Increment counter metric."""
        with self._lock:
            self._counters[metric_name] += value
    
    def start_timer(self, timer_name: str) -> None:
        """Start timing an operation."""
        self._start_times[timer_name] = time.perf_counter()
    
    def stop_timer(self, timer_name: str) -> float:
        """Stop timing and record duration."""
        if timer_name not in self._start_times:
            return 0.0
        
        duration = time.perf_counter() - self._start_times.pop(timer_name)
        
        with self._lock:
            self._timers[timer_name].append(duration)
        
        return duration
    
    def record_duration(self, timer_name: str, duration: float) -> None:
        """Directly record a duration measurement."""
        with self._lock:
            self._timers[timer_name].append(duration)
    
    def get_counter(self, metric_name: str) -> int:
        """Get current counter value."""
        with self._lock:
            return self._counters.get(metric_name, 0)
    
    def get_timer_stats(self, timer_name: str) -> Dict[str, float]:
        """Get statistics for timer (avg, min, max, count)."""
        with self._lock:
            measurements = list(self._timers.get(timer_name, []))
        
        if not measurements:
            return {
                'count': 0,
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'total': 0.0
            }
        
        return {
            'count': len(measurements),
            'avg': sum(measurements) / len(measurements),
            'min': min(measurements),
            'max': max(measurements),
            'total': sum(measurements)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            counters = dict(self._counters)
            timers = {name: list(values) for name, values in self._timers.items()}
        
        return {
            'counters': counters,
            'timers': timers,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._timers.clear()
            self._start_times.clear()


class PerformanceMonitor:
    """Central performance monitoring service."""
    
    _instance: Optional['PerformanceMonitor'] = None
    _instance_lock = threading.Lock()
    
    def __new__(cls) -> 'PerformanceMonitor':
        """Thread-safe singleton implementation."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.metrics = PerformanceMetrics()
            self.enabled = True
            self.initialized = True
    
    def profile(self, name: Optional[str] = None) -> Callable:
        """
        Decorator to profile function execution time.
        
        Usage:
            @monitor.profile("my_function")
            def my_function():
                pass
        """
        def decorator(func: Callable) -> Callable:
            metric_name = name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                start_time = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start_time
                    self.metrics.record_duration(metric_name, duration)
                    logger.debug(f"Performance: {metric_name} took {duration:.4f}s")
            
            return wrapper
        return decorator
    
    def timed_block(self, name: str) -> 'TimedBlock':
        """
        Context manager for timing code blocks.
        
        Usage:
            with monitor.timed_block("database_query"):
                result = db.query()
        """
        return TimedBlock(self, name)
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment named counter."""
        if self.enabled:
            self.metrics.increment(name, value)
    
    def record_cache_hit(self, cache_level: str = "L1") -> None:
        """Record cache hit event."""
        self.increment_counter(f"cache.{cache_level.lower()}.hits")
    
    def record_cache_miss(self, cache_level: str = "L1") -> None:
        """Record cache miss event."""
        self.increment_counter(f"cache.{cache_level.lower()}.misses")
    
    def get_cache_hit_ratio(self, cache_level: str = "L1") -> float:
        """Calculate cache hit ratio (0.0 to 1.0)."""
        hits = self.metrics.get_counter(f"cache.{cache_level.lower()}.hits")
        misses = self.metrics.get_counter(f"cache.{cache_level.lower()}.misses")
        total = hits + misses
        
        return hits / total if total > 0 else 0.0
    
    def get_report(self) -> Dict[str, Any]:
        """Generate complete performance report."""
        metrics = self.metrics.get_all_metrics()
        
        # Calculate derived metrics
        cache_stats = {
            'L1': {
                'hits': self.metrics.get_counter("cache.l1.hits"),
                'misses': self.metrics.get_counter("cache.l1.misses"),
                'hit_ratio': self.get_cache_hit_ratio("L1")
            },
            'L2': {
                'hits': self.metrics.get_counter("cache.l2.hits"),
                'misses': self.metrics.get_counter("cache.l2.misses"),
                'hit_ratio': self.get_cache_hit_ratio("L2")
            }
        }
        
        return {
            'metrics': metrics,
            'cache_stats': cache_stats,
            'generated_at': datetime.now().isoformat()
        }
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        self.metrics.reset()
        logger.info("Performance metrics reset")


class TimedBlock:
    """Context manager for timing code blocks."""
    
    def __init__(self, monitor: PerformanceMonitor, name: str):
        self.monitor = monitor
        self.name = name
        self.start_time = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.monitor.metrics.record_duration(self.name, duration)
        return False  # Don't suppress exceptions


# Global monitor instance
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Legacy compatibility factory function"""
    return performance_monitor


# Convenience decorator
profile = performance_monitor.profile

# Convenience context manager
timed_block = performance_monitor.timed_block
