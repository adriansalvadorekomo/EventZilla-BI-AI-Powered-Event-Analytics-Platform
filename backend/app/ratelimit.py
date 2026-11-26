"""A small sliding-window limiter for the analyst endpoint.

Each question calls an LLM with the owner's key, so a public deployment limits it per visitor and per instance.
Limits come from the environment (ASK_LIMIT questions per ASK_WINDOW_S seconds per visitor; ASK_INSTANCE_LIMIT per
window for everyone). State is in memory: on a serverless platform each instance counts for itself, which is enough
to stop casual abuse; add a platform rate-limit rule for a hard guarantee.
"""

import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request


class SlidingWindow:
    def __init__(self, limit: int, window_s: int, instance_limit: int):
        self.limit, self.window_s, self.instance_limit = limit, window_s, instance_limit
        self._hits: dict[str, deque] = defaultdict(deque)
        self._all: deque = deque()
        self._lock = Lock()

    @staticmethod
    def client_id(request: Request) -> str:
        """The visitor behind the proxy, taken only from headers a client cannot forge.

        Vercel sets x-vercel-forwarded-for and x-real-ip itself. Behind nginx the address nginx saw is the LAST entry
        of X-Forwarded-For (a client can put anything in the first ones), so the last entry is used, never the first.
        """
        h = request.headers
        if h.get("x-vercel-forwarded-for"):
            return h["x-vercel-forwarded-for"].split(",")[0].strip()
        if h.get("x-real-ip"):
            return h["x-real-ip"].strip()
        forwarded = [p.strip() for p in h.get("x-forwarded-for", "").split(",") if p.strip()]
        return forwarded[-1] if forwarded else (request.client.host if request.client else "unknown")

    def check(self, who: str, now: float | None = None) -> tuple[bool, int]:
        """(allowed, seconds to wait). Records the hit only when allowed."""
        now = time.monotonic() if now is None else now
        with self._lock:
            for queue in (self._hits[who], self._all):
                while queue and now - queue[0] >= self.window_s:
                    queue.popleft()
            mine = self._hits[who]
            if len(mine) >= self.limit:
                return False, max(1, int(self.window_s - (now - mine[0])))
            if len(self._all) >= self.instance_limit:
                return False, max(1, int(self.window_s - (now - self._all[0])))
            mine.append(now)
            self._all.append(now)
            if not mine and who in self._hits:
                del self._hits[who]
            return True, 0


ask_limiter = SlidingWindow(
    limit=int(os.environ.get("ASK_LIMIT", "8")),
    window_s=int(os.environ.get("ASK_WINDOW_S", "600")),
    instance_limit=int(os.environ.get("ASK_INSTANCE_LIMIT", "60")),
)
