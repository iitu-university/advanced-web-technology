"""Count SQL statements executed while handling each HTTP request."""

from contextvars import ContextVar

from fastapi import FastAPI
from sqlalchemy import event

from db import engine

_current = ContextVar("sql_query_counter", default=None)


@event.listens_for(engine, "before_cursor_execute")
def _count_query(conn, cursor, statement, parameters, context, executemany):
    counter = _current.get()
    if counter is not None:
        counter["count"] += 1


class SQLCounterMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        counter = {"count": 0}
        token = _current.set(counter)

        async def send_with_count(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-sql-queries", str(counter["count"]).encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_count)
        finally:
            _current.reset(token)


def install(app: FastAPI) -> None:
    app.add_middleware(SQLCounterMiddleware)
