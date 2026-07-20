"""
threading_utils.py — Thread-safe data structures and decorators.
Provides ThreadSafeDict, AtomicBool, AtomicValue, and @thread_safe decorator.
"""
import threading
from typing import Any, Callable, Dict, Optional, TypeVar

F = TypeVar('F', bound=Callable[..., Any])


class ThreadSafeDict:
    """A dict wrapper using threading.RLock for thread-safe read/write."""
    
    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)
        self._lock = threading.RLock()
    
    def __getitem__(self, key):
        with self._lock:
            return self._dict[key]
    
    def __setitem__(self, key, value):
        with self._lock:
            self._dict[key] = value
    
    def __contains__(self, key):
        with self._lock:
            return key in self._dict
    
    def get(self, key, default=None):
        with self._lock:
            return self._dict.get(key, default)
    
    def pop(self, key, default=None):
        with self._lock:
            return self._dict.pop(key, default)
    
    def keys(self):
        with self._lock:
            return list(self._dict.keys())
    
    def values(self):
        with self._lock:
            return list(self._dict.values())
    
    def items(self):
        with self._lock:
            return list(self._dict.items())
    
    def copy(self):
        with self._lock:
            return self._dict.copy()
    
    def clear(self):
        with self._lock:
            self._dict.clear()
    
    def update(self, other=None, **kwargs):
        with self._lock:
            self._dict.update(other or {}, **kwargs)
    
    def __len__(self):
        with self._lock:
            return len(self._dict)
    
    def __repr__(self):
        with self._lock:
            return repr(self._dict)
    
    def __iter__(self):
        with self._lock:
            return iter(list(self._dict.keys()))


class AtomicBool:
    """Thread-safe boolean wrapper using a lock."""
    
    def __init__(self, initial: bool = False):
        self._value = bool(initial)
        self._lock = threading.Lock()
    
    @property
    def value(self) -> bool:
        with self._lock:
            return self._value
    
    @value.setter
    def value(self, new_value: bool):
        with self._lock:
            self._value = bool(new_value)
    
    def set(self):
        with self._lock:
            self._value = True
    
    def clear(self):
        with self._lock:
            self._value = False
    
    def __bool__(self):
        return self.value
    
    def __eq__(self, other):
        return self.value == bool(other)


class AtomicValue:
    """Thread-safe wrapper for any value type."""
    
    def __init__(self, initial=None):
        self._value = initial
        self._lock = threading.Lock()
    
    @property
    def value(self):
        with self._lock:
            return self._value
    
    @value.setter
    def value(self, new_value):
        with self._lock:
            self._value = new_value
    
    def __eq__(self, other):
        return self.value == other


def thread_safe(lock_attr: str = "_lock"):
    """
    Decorator that wraps a method with a threading lock.
    The lock is accessed via self.<lock_attr>.
    """
    def decorator(func: F) -> F:
        def wrapper(self, *args, **kwargs):
            lock = getattr(self, lock_attr)
            with lock:
                return func(self, *args, **kwargs)
        return wrapper  # type: ignore
    return decorator
