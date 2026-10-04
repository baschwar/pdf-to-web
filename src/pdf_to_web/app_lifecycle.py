"""Graceful shutdown of one explicitly owned server, without process discovery."""
from __future__ import annotations

import threading
from collections.abc import Callable


class QuitUnavailable(ValueError):
    pass


class OwnedServerLifecycle:
    def __init__(self, stop: Callable[[], None] | None = None):
        self._stop = stop
        self._lock = threading.RLock()
        self._active = 0
        self._stopping = False
        self._error = ''

    def bind(self, stop: Callable[[], None]) -> None:
        with self._lock:
            self._stop = stop

    def status(self) -> dict:
        with self._lock:
            return {'available': self._stop is not None, 'state': 'stopping' if self._stopping else 'running',
                    'active_work': self._active, 'error': self._error}

    def start_work(self) -> bool:
        with self._lock:
            if self._stopping:
                return False
            self._active += 1
            return True

    def finish_work(self) -> None:
        with self._lock:
            self._active -= 1

    def prepare_quit(self) -> None:
        with self._lock:
            if self._stop is None:
                raise QuitUnavailable('Quit is unavailable for this externally managed server. Stop its own launcher instead.')
            if self._stopping:
                raise QuitUnavailable('Quit has already been requested. Wait for this app to stop.')
            if self._active:
                raise QuitUnavailable('Work is still in progress. Wait for processing, saves, downloads and image generation to finish, then try Quit again.')
            self._error = ''
            self._stopping = True

    def stop(self) -> None:
        # Invoked after the quit response is sent. Only the bound server is touched.
        try:
            self._stop()
        except Exception:
            with self._lock:
                self._stopping = False
                self._error = 'PDF to Web could not stop its server. Your work is still available; retry Quit or stop its own launcher.'


class LifecycleMiddleware:
    """Hold work admission until the complete ASGI response/background work ends."""
    def __init__(self, app, lifecycle: OwnedServerLifecycle):
        self.app = app
        self.lifecycle = lifecycle

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] in {'/api/lifecycle', '/api/quit', '/api/health'}:
            return await self.app(scope, receive, send)
        if not self.lifecycle.start_work():
            from starlette.responses import JSONResponse
            return await JSONResponse({'detail': 'PDF to Web is quitting. New work is unavailable.'}, status_code=409)(scope, receive, send)
        try:
            await self.app(scope, receive, send)
        finally:
            self.lifecycle.finish_work()
