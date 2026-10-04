"""Sessões locais com turnos completos, TTL e exclusão mútua por gestor/chat."""

import asyncio
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from time import monotonic


class SessionsBusy(RuntimeError):
    pass


@dataclass
class Session:
    turns: deque
    touched: float
    borrowers: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def history(self):
        return [message for turn in self.turns for message in turn]


class SessionStore:
    def __init__(self, max_sessions=1000, max_turns=8, ttl=3600, clock=monotonic):
        self.items = OrderedDict()
        self.max_sessions, self.max_turns, self.ttl = max_sessions, max_turns, ttl
        self.clock = clock

    @asynccontextmanager
    async def acquire(self, key):
        now = self.clock()
        for old_key, value in list(self.items.items()):
            if value.borrowers == 0 and now - value.touched > self.ttl:
                del self.items[old_key]
        if key not in self.items:
            if len(self.items) >= self.max_sessions:
                evict = next((k for k, v in self.items.items() if v.borrowers == 0), None)
                if evict is None:
                    raise SessionsBusy("Todas as sessões estão ocupadas. Tente novamente.")
                del self.items[evict]
            self.items[key] = Session(deque(maxlen=self.max_turns), now)
        session = self.items[key]
        # Conta também os que aguardam lock, para impedir remoção durante uma fila.
        session.borrowers += 1
        try:
            async with session.lock:
                yield session
        finally:
            session.borrowers -= 1
            session.touched = self.clock()
            self.items.move_to_end(key)
