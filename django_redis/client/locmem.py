import time

from django.core.cache.backends.locmem import LocMemCache, DEFAULT_TIMEOUT

from ..client import DefaultClient


class LocMemCacheEx(LocMemCache):

    @property
    def expire_info(self):
        return self._expire_info

    def delete_many(self, keys, version=None):
        super().delete_many(keys, version=version)
        return True

    def delete_pattern(self, pattern, version=None):
        keys = self.keys(pattern, version=version)
        return self.delete_many(keys, version=version)

    def expire(self, key, timeout, version=None):
        k = self.make_key(key, version=version)
        self._expire_info[k] = self.get_backend_timeout(timeout)

    def incr(self, key, delta=1, version=None, ignore_key_check=False):
        if ignore_key_check and not self.has_key(key, version=version):
            return self.set(key, delta, version=version)
        return super().incr(key, delta=delta, version=version)

    def keys(self, search, version=None):
        if not search or search == '*':
            return self._cache.keys()
        import re
        s = self.make_key(search, version=version)
        matcher = re.compile(s)
        return [key for key in self._cache.keys() if matcher.match(key)]

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        """RedisClient 'set' returns the value"""
        if timeout == -1:
            timeout = 0
        super().set(key, value, timeout=timeout, version=version)
        return self.get('key', default=value, version=version)

    def ttl(self, key, version=None):
        k = self.make_key(key, version=version)
        exp = self._expire_info.get(k, -1)
        if exp is None:
            return None
        if exp == -1 or exp == 0:
            return 0
        timeout = exp - time.time()
        return max(0, timeout)


class LocMemClient(DefaultClient):
    """ RedisClient that uses django LocMem backend - useful for unit tests
    To use this pass the FQN in CLIENT_CLASS entry of OPTIONS
    example:
    CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.LocMemClient',
            'IGNORE_EXCEPTIONS': True
        }
    }
    """
    def __init__(self, servers, params, *args, **kwargs):
        super().__init__(servers, params, *args, **kwargs)
        name = servers[0] if isinstance(servers, list) else servers
        self._cache = LocMemCacheEx(name, params)

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None, **kwargs):
        if self._cache.has_key(key, version):
            return False
        return self._cache.add(key, value, timeout=timeout, version=version)

    def connect(self, index=0):
        raise Exception('UnsupportedOperation: connect')

    def decr(self, key, *args, delta=1, version=None, **kwargs):
        return self._cache.decr(key, delta=delta, version=version)

    def delete(self, key, version=None, **kwargs):
        return self._cache.delete(key, version=self)

    def delete_many(self, keys, version=None, **kwargs):
        return self._cache.delete_many(keys, version=version)

    def delete_pattern(self, pattern, version=None, prefix=None, client=None, itersize=None, **kwargs):
        return self._cache.delete_pattern(pattern, version=version)

    def expire(self, key, timeout, version=None, **kwargs):
        return self._cache.expire(key, timeout, version=version)

    def get(self, key, default=None, version=None, **kwargs):
        return self._cache.get(key, default=default, version=version)

    def get_many(self, keys, version=None, **kwargs):
        return self._cache.get_many(keys, version=version)

    def clear(self, **kwargs):
        return self._cache.clear()

    def get_client(self, write=True, tried=(), show_index=False):
        return self

    def has_key(self, key, version=None, **kwargs):
        return self._cache.has_key(key, version=version)

    def incr(self, key, *args, delta=1, version=None, ignore_key_check=False, **kwargs):
        return self._cache.incr(key, delta=delta, version=version, ignore_key_check=ignore_key_check)

    def incr_version(self, key, delta=1, version=None, **kwargs):
        return self._cache.incr_version(key, delta=delta, version=version)

    def iter_keys(self, search, itersize=None, client=None, version=None):
        raise Exception('UnsupportedOperation: iter_keys')

    def keys(self, search, version=None, **kwargs):
        return self._cache.keys(search, version=version)

    def lock(self, key, version=None, timeout=None, sleep=0.1, blocking_timeout=None, client=None, thread_local=True):
        raise Exception('UnsupportedOperation: lock')

    def persist(self, key, version=None, **kwargs):
        raise Exception('UnsupportedOperation: persist')

    def pipeline(self):
        raise Exception('UnsupportedOperation: pipeline')

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None, **kwargs):
        return self._cache.set(key, value, timeout=timeout, version=version)

    def set_many(self, data, *args, timeout=DEFAULT_TIMEOUT, version=None, **kwargs):
        return self._cache.set_many(data, timeout=timeout, version=version)

    def scan(self, **kwargs):
        raise Exception('UnsupportedOperation: scan')

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None, **kwargs):
        return self._cache.touch(key, timeout=timeout, version=version)

    def ttl(self, key, version=None, **kargs):
        return self._cache.ttl(key, version=version)
