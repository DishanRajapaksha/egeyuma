from __future__ import annotations

from collections.abc import Callable

LogFn = Callable[[str], None]


def null_log(message: str) -> None:
    return None
