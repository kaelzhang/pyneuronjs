

# Memoize the result of the function
def memoize(fn):
    def method(self, *args):
        # prevent saving cache for empty facades
        if not self.cache or not len(self.facades):
            return fn(self, *args)

        hash_id = self._get_identifier_hash()
        if self.cache.has(hash_id):
            return self.cache.get(hash_id)

        result = fn(self, *args)
        self.cache.save(hash_id, result)
        return result

    return method


def beforeoutput(fn):
    def method(self, *args):
        if self._outputted:
            return ''
        return fn(self, *args)

    return method


def beforecssoutput(fn):
    return fn
