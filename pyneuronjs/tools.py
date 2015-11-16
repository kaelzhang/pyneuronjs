# decorators

import functools

# Memoize the result of the function
def memoize(cache_key_getter):
    """ Decorator: memoize the result of a function by
        the key which is generated from `cache_key_getter`

        - cache_key_getter `String|function()`
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args):
            # prevent saving cache for empty facades
            if not self.cache or not len(self.facades):
                return fn(self, *args)

            hash_id = getattr(self, cache_key_getter)()
            result = self.cache.get(hash_id);
            if result:
                return result

            result = fn(self, *args)
            self.cache.save(hash_id, result)
            return result
        return wrapper
    return decorator


def before_analyze(fn):
    @functools.wraps(fn)
    def method(self, *args):
        if self._analyzed:
            return ''
        return fn(self, *args)
    return method
