#!/usr/bin/env python3

import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps

class Cache:
    """Cache class to store data in Redis with unique keys."""

    def __init__(self):
        """Initialize Redis client and flush the database."""
        self._redis = redis.Redis()
        self._redis.flushdb()

    def store(self, data: 'str | bytes | int | float') -> str:
        """Store data in Redis and return the generated key."""
        key = str(uuid.uuid4())  # Generate a random key
        self._redis.set(key, data)  # Store data with the key
        return key

    def get(self, key: str, fn: callable = None) -> 'str | bytes | int | float':
        """Retrieve data from Redis and convert it using a callable if provided."""
        value = self._redis.get(key)
        if value is None:
            return None
        if fn:
            return fn(value)
        return value

    def get_str(self, key: str) -> str:
        """Retrieve a string from Redis."""
        return self.get(key, fn=lambda d: d.decode('utf-8'))

    def get_int(self, key: str) -> int:
        """Retrieve an integer from Redis."""
        return self.get(key, fn=int)

def count_calls(method: Callable) -> Callable:
    ''' def count calls '''
    @wraps(method)
    def wrapper(self, *args, **kwds):
        ''' def wrapper '''
        key_name = method.__qualname__
        self._redis.incr(key_name, 0) + 1
        return method(self, *args, **kwds)
    return wrapper

def call_history(method: Callable) -> Callable:
    ''' def call history '''
    @wraps(method)
    def wrapper(self, *args, **kwds):
        ''' def wrapper'''
        key_m = method.__qualname__
        inp_m = key_m + ':inputs'
        outp_m = key_m + ":outputs"
        data = str(args)
        self._redis.rpush(inp_m, data)
        fin = method(self, *args, **kwds)
        self._redis.rpush(outp_m, str(fin))
        return fin
    return wrapper

def replay(func: Callable):
    '''def replay'''
    r = redis.Redis()
    key_m = func.__qualname__
    inp_m = r.lrange("{}:inputs".format(key_m), 0, -1)
    outp_m = r.lrange("{}:outputs".format(key_m), 0, -1)
    calls_number = len(inp_m)
    times_str = 'times'
    if calls_number == 1:
        times_str = 'time'
    fin = '{} was called {} {}:'.format(key_m, calls_number, times_str)
    print(fin)
    for k, v in zip(inp_m, outp_m):
        fin = '{}(*{}) -> {}'.format(
            key_m,
            k.decode('utf-8'),
            v.decode('utf-8')
        )
        print(fin)
