#!/usr/bin/env python3
import redis
import uuid
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

def count_calls(method):
    """Decorator to count calls to a method."""
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Wrap the method and increment the call count."""
        self._redis.incr(key)
        return method(self, *args, **kwargs)

    return wrapper

# Decorate the store method
Cache.store = count_calls(Cache.store)

def call_history(method):
    """Decorator to store input/output history of a method."""
    input_key = f"{method.__qualname__}:inputs"
    output_key = f"{method.__qualname__}:outputs"

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Wrap the method to log inputs and outputs."""
        # Store input as string
        self._redis.rpush(input_key, str(args))
        # Call the original method
        output = method(self, *args, **kwargs)
        # Store output
        self._redis.rpush(output_key, output)
        return output

    return wrapper

# Apply the call_history decorator
Cache.store = call_history(Cache.store)

def replay(method):
    """Display the call history for a method."""
    inputs = method.__self__._redis.lrange(f"{method.__qualname__}:inputs", 0, -1)
    outputs = method.__self__._redis.lrange(f"{method.__qualname__}:outputs", 0, -1)

    count = len(inputs)
    print(f"{method.__qualname__} was called {count} times:")
    
    for inp, out in zip(inputs, outputs):
        print(f"{method.__qualname__}(*{inp.decode()}) -> {out.decode()}")
