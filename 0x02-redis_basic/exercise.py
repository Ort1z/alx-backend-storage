#!/usr/bin/env python3
"""
Redis basic exercises - implementing a Cache class with counting decorator
"""
import redis
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts how many times a method is called.
    
    Args:
        method: The method to be decorated
        
    Returns:
        Callable: The wrapped function
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper function that increments the call count and executes the method.
        
        Args:
            self: Instance of the Cache class
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
            
        Returns:
            Any: Result from the wrapped method
        """
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


class Cache:
    """
    Cache class to handle redis operations
    """
    def __init__(self) -> None:
        """
        Initialize the Cache instance.
        Creates a Redis client and flushes the database.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis using a random key.
        
        Args:
            data: Data to be stored (can be str, bytes, int, or float)
            
        Returns:
            str: Key under which the data was stored
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, 
            fn: Optional[Callable] = None) -> Union[str, bytes, int, float]:
        """
        Retrieve data from Redis.
        
        Args:
            key: Key to look up in Redis
            fn: Optional callable to transform the retrieved data
            
        Returns:
            Union[str, bytes, int, float]: Retrieved data
        """
        data = self._redis.get(key)
        if fn:
            return fn(data)
        return data