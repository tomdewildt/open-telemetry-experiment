import time

from loguru import logger
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class AccessLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        start_time = time.perf_counter()
        status_code = 500  # Set by _send in happy flow

        async def _send(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception as exc:
            raise exc
        finally:
            end_time = time.perf_counter()
            self.log(scope, status_code, start_time, end_time)

    @staticmethod
    def log(scope: Scope, status_code: int, start_time: float, end_time: float) -> None:
        client = scope.get("client")
        logger.info(
            "{client} - {method} {path} {status_code} ({duration:.0f}ms)",
            client=f"{client[0]}:{client[1]}" if client else "-",
            method=scope["method"],
            path=scope["path"],
            status_code=status_code,
            duration=(end_time - start_time) * 1000,
        )
