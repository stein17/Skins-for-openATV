from __future__ import absolute_import

import time

try:
    from urllib.parse import quote as _urlquote
except ImportError:
    from urllib import quote as _urlquote


API_PROXY_BASE = "https://gradient-api-proxy.lutzkroll.chatgpt.site"
FALLBACK_API_MARKER = "gradient-default-proxy"

# If the shared fallback service is unavailable, do not repeat the same slow
# request for every event/provider. Direct requests with a user-supplied key
# never use this circuit breaker.
PROXY_FAILURE_COOLDOWN = 60 * 60
PROXY_CONNECT_TIMEOUT = 2.5
PROXY_READ_TIMEOUT = 5.0
_proxy_disabled_until = 0.0


class GradientAPIProxyUnavailable(IOError):
    pass


def reset_proxy_circuit():
    global _proxy_disabled_until
    _proxy_disabled_until = 0.0


def _proxy_circuit_open():
    try:
        return time.time() < _proxy_disabled_until
    except Exception:
        return False


def _disable_proxy_temporarily():
    global _proxy_disabled_until
    try:
        _proxy_disabled_until = time.time() + PROXY_FAILURE_COOLDOWN
    except Exception:
        _proxy_disabled_until = 0.0


def _bounded_proxy_timeout(value):
    connect_timeout = PROXY_CONNECT_TIMEOUT
    read_timeout = PROXY_READ_TIMEOUT
    try:
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            connect_timeout = min(float(value[0]), PROXY_CONNECT_TIMEOUT)
            read_timeout = min(float(value[1]), PROXY_READ_TIMEOUT)
        elif value is not None:
            timeout = min(float(value), PROXY_READ_TIMEOUT)
            connect_timeout = min(timeout, PROXY_CONNECT_TIMEOUT)
            read_timeout = timeout
    except Exception:
        pass
    return (max(0.5, connect_timeout), max(1.0, read_timeout))


def _proxy_response_failed(response):
    try:
        status = int(getattr(response, "status_code", 0) or 0)
    except Exception:
        status = 0
    try:
        headers = getattr(response, "headers", {}) or {}
        if str(headers.get("x-gradient-proxy-error", "")) == "1":
            return True
    except Exception:
        pass
    return status in (401, 403, 408, 429) or status >= 500


def _fallback_request(call, url, args, kwargs):
    if _proxy_circuit_open():
        raise GradientAPIProxyUnavailable("Gradient fallback API proxy disabled after previous failure")

    call_kwargs = dict(kwargs)
    call_kwargs["timeout"] = _bounded_proxy_timeout(call_kwargs.get("timeout"))
    try:
        response = call(proxy_url(url, call_kwargs), *args, **call_kwargs)
    except Exception:
        _disable_proxy_temporarily()
        raise
    if _proxy_response_failed(response):
        _disable_proxy_temporarily()
    return response


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
    def __init__(self, session, requests_module):
        self._session = session
        self._requests = requests_module

    def get(self, url, *args, **kwargs):
        if not _uses_fallback(url, kwargs):
            return self._session.get(url, *args, **kwargs)
        return _fallback_request(self._requests.get, url, args, kwargs)

    def post(self, url, *args, **kwargs):
        if not _uses_fallback(url, kwargs):
            return self._session.post(url, *args, **kwargs)
        return _fallback_request(self._requests.post, url, args, kwargs)

    def request(self, method, url, *args, **kwargs):
        if not _uses_fallback(url, kwargs):
            return self._session.request(method, url, *args, **kwargs)
        call = lambda target, *a, **kw: self._requests.request(method, target, *a, **kw)
        return _fallback_request(call, url, args, kwargs)

    def __getattr__(self, name):
        return getattr(self._session, name)


class _RequestsProxy(object):
    def __init__(self, requests_module):
        self._requests = requests_module

    def Session(self, *args, **kwargs):
        return _SessionProxy(self._requests.Session(*args, **kwargs), self._requests)

    def get(self, url, *args, **kwargs):
        if not _uses_fallback(url, kwargs):
            return self._requests.get(url, *args, **kwargs)
        return _fallback_request(self._requests.get, url, args, kwargs)

    def post(self, url, *args, **kwargs):
        if not _uses_fallback(url, kwargs):
            return self._requests.post(url, *args, **kwargs)
        return _fallback_request(self._requests.post, url, args, kwargs)

    def request(self, method, url, *args, **kwargs):
        if not _uses_fallback(url, kwargs):
            return self._requests.request(method, url, *args, **kwargs)
        call = lambda target, *a, **kw: self._requests.request(method, target, *a, **kw)
        return _fallback_request(call, url, args, kwargs)

    def __getattr__(self, name):
        return getattr(self._requests, name)


def wrap_requests(requests_module):
    return _RequestsProxy(requests_module)


def wrap_get(get_function):
    def wrapped(url, *args, **kwargs):
        if not _uses_fallback(url, kwargs):
            return get_function(url, *args, **kwargs)
        return _fallback_request(get_function, url, args, kwargs)
    return wrapped
