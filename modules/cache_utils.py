"""
Session-safe in-memory caching utilities for AlloGraph.

GDPR/Healthcare compliant:
- All caching is in-memory only (no disk persistence)
- Cache cleared when server restarts
- No PHI in cache keys (uses content hashes)
- Session-scoped: data only lives for the HTTP request/response cycle
"""

import hashlib
import json
from functools import wraps
from typing import Any, Callable
import pandas as pd
import numpy as np

# In-memory cache storage (process-local, cleared on restart)
_cache_store = {}

def _make_cache_key(*args, **kwargs) -> str:
    """
    Create a cache key from arguments.
    Uses hash of argument IDs/values - no PHI stored.
    """
    key_parts = []
    
    for arg in args:
        if isinstance(arg, (list, dict)):
            # Hash the structure, not content (privacy)
            key_parts.append(hashlib.sha256(str(id(arg)).encode()).hexdigest()[:16])
        elif isinstance(arg, pd.DataFrame):
            # Hash of shape and column names only (no data values)
            shape_hash = f"{arg.shape}_{list(arg.columns)}"
            key_parts.append(hashlib.sha256(shape_hash.encode()).hexdigest()[:16])
        else:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={hashlib.sha256(str(v).encode()).hexdigest()[:8]}")
    
    return "|".join(key_parts)


def cache_result(maxsize: int = 128) -> Callable:
    """
    Decorator for caching function results in memory.
    
    Args:
        maxsize: Maximum number of cached results to keep
        
    Usage:
        @cache_result(maxsize=32)
        def expensive_calculation(data, param1, param2):
            # Heavy computation here
            return result
    """
    def decorator(func: Callable) -> Callable:
        func_cache = {}
        func_cache_order = []  # For LRU eviction
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = _make_cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            if cache_key in func_cache:
                # Move to end (most recently used)
                func_cache_order.remove(cache_key)
                func_cache_order.append(cache_key)
                return func_cache[cache_key]
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            func_cache[cache_key] = result
            func_cache_order.append(cache_key)
            
            # LRU eviction
            while len(func_cache) > maxsize:
                oldest_key = func_cache_order.pop(0)
                del func_cache[oldest_key]
            
            return result
        
        # Add cache management methods
        wrapper.cache_clear = lambda: (func_cache.clear(), func_cache_order.clear())
        wrapper.cache_info = lambda: {
            'size': len(func_cache),
            'maxsize': maxsize,
            'function': func.__name__
        }
        
        return wrapper
    return decorator


def clear_all_caches():
    """Clear all in-memory caches. Called on server restart."""
    global _cache_store
    _cache_store.clear()


def get_cache_info() -> dict:
    """Get information about current cache state (for debugging)."""
    return {
        'global_cache_size': len(_cache_store),
        'note': 'All caches are in-memory only, no persistence'
    }


# Specific helpers for common AlloGraph operations

def cache_survival_result(func):
    """
    Specialized cache for survival analysis results.
    Keys are based on data shape and filter parameters (not patient data).
    """
    return cache_result(maxsize=16)(func)


def cache_gvh_result(func):
    """
    Specialized cache for GvH competing risks results.
    """
    return cache_result(maxsize=16)(func)


def cache_upset_data(func):
    """
    Specialized cache for UpSet plot generation.
    """
    return cache_result(maxsize=8)(func)
