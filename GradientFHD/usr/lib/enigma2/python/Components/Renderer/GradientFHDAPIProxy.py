from __future__ import absolute_import

try:
    from urllib.parse import quote as _urlquote
except ImportError:
    from urllib import quote as _urlquote


API_PROXY_BASE = "https://gradient-api-proxy.lutzkroll.chatgpt.site"
FALLBACK_API_MARKER = "gradient-default-proxy"


def _uses_fallback(url, kwargs):
    if FALLBACK_API_MARKER in str(url or ""):
        return True
    for name in ("data", "json"):
        value = kwargs.get(name)
        if value is not None and FALLBACK_API_MARKER in str(value):
            return True
    return False


def proxy_url(url, kwargs=None):
    kwargs = kwargs or {}
    if not _uses_fallback(url, kwargs):
        return url
    return "%s/v1/fetch?target=%s" % (
        API_PROXY_BASE.rstrip("/"),
        _urlquote(str(url), safe=""),
    )


class _SessionProxy(object):
    def __init__(self, session):
        self._session = session

    def get(self, url, *args, **kwargs):
        return self._session.get(proxy_url(url, kwargs), *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._session.post(proxy_url(url, kwargs), *args, **kwargs)

    def request(self, method, url, *args, **kwargs):
        return self._session.request(method, proxy_url(url, kwargs), *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._session, name)


class _RequestsProxy(object):
    def __init__(self, requests_module):
        self._requests = requests_module

    def Session(self, *args, **kwargs):
        return _SessionProxy(self._requests.Session(*args, **kwargs))

    def get(self, url, *args, **kwargs):
        return self._requests.get(proxy_url(url, kwargs), *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._requests.post(proxy_url(url, kwargs), *args, **kwargs)

    def request(self, method, url, *args, **kwargs):
        return self._requests.request(method, proxy_url(url, kwargs), *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._requests, name)


def wrap_requests(requests_module):
    return _RequestsProxy(requests_module)


def wrap_get(get_function):
    def wrapped(url, *args, **kwargs):
        return get_function(proxy_url(url, kwargs), *args, **kwargs)
    return wrapped
