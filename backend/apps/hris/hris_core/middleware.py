"""
AuditMiddleware
===============
Stores the current HTTP request in a thread-local variable so that
signals (which have no access to the request) can read the acting user
and IP address when writing audit log entries.
"""
import threading

_thread_local = threading.local()


def get_current_request():
    return getattr(_thread_local, "request", None)


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.request = request
        try:
            response = self.get_response(request)
        finally:
            _thread_local.request = None
        return response
