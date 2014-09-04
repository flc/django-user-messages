try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.4 fallback.

from django.db.models import Count


def cached_attribute(func):
    cache_name = "_%s" % func.__name__

    @wraps(func)
    def inner(self, *args, **kwargs):
        if hasattr(self, cache_name):
            return getattr(self, cache_name)
        val = func(self, *args, **kwargs)
        setattr(self, cache_name, val)
        return val
    return inner


def get_m2m_exact_match(model_class, m2m_field, ids):
    # can produce q huge query with lots of len(ids) inner joins
    # consider some sort of unique, consistent hash of ids
    query = model_class.objects.annotate(count=Count(m2m_field)).filter(count=len(ids))
    for _id in ids:
        query = query.filter(**{"{}__id".format(m2m_field): _id})
    return query
