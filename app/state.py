import asyncio
import logging
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from time import monotonic

import psycopg
from psycopg.types.json import Jsonb

from app.sessions import Session, SessionsBusy

logger = logging.getLogger(__name__)

RECEIVED, DUPLICATE, FULL = "received", "duplicate", "full"
BUSY_MESSAGE = "Sua pergunta anterior ainda está sendo processada. Tente novamente em instantes."


class MemoryInbox:
    def __init__(self, max_pending=100, seen_ttl=86400, seen_max=10000):
        self.queue = asyncio.Queue(maxsize=max_pending)
        self.seen = OrderedDict()
        self.seen_ttl, self.seen_max = seen_ttl, seen_max

    async def start(self):
        pass

    async def close(self):
        pass

    async def register(self, update_id, payload):
        now = monotonic()
        for old_id, timestamp in list(self.seen.items()):
            if now - timestamp > self.seen_ttl:
                del self.seen[old_id]
        if update_id in self.seen:
            return DUPLICATE
        if self.queue.full():
            return FULL
        self.seen[update_id] = now
        if len(self.seen) > self.seen_max:
            self.seen.popitem(last=False)
        self.queue.put_nowait((update_id, payload))
        return RECEIVED

    async def next(self):
        return await self.queue.get()

    async def done(self, update_id):
        self.queue.task_done()

    async def retry(self, update_id):
        self.seen.pop(update_id, None)
        self.queue.task_done()

    async def join(self):
        await self.queue.join()


class _Db:
    def __init__(self, dsn):
        self.dsn, self._conn, self._lock = dsn, None, asyncio.Lock()

    def _run(self, query, params):
        for attempt in (0, 1):
            try:
                if self._conn is None or self._conn.closed:
                    self._conn = psycopg.connect(self.dsn, autocommit=True, connect_timeout=5)
                cursor = self._conn.execute(query, params)
                return cursor.fetchall() if cursor.description else []
            except psycopg.OperationalError:
                self._close()
                if attempt:
                    raise

    def _close(self):
        conn, self._conn = self._conn, None
        if conn is not None and not conn.closed:
            try:
                conn.close()
            except psycopg.Error:
                pass

    async def execute(self, query, params=()):
        async with self._lock:
            return await asyncio.to_thread(self._run, query, params)

    async def close(self):
        async with self._lock:
            await asyncio.to_thread(self._close)


class PostgresInbox:
    def __init__(
        self,
        dsn,
        *,
        max_pending=100,
        lease_seconds=180,
        max_attempts=3,
        poll_interval=1.0,
        retention_seconds=86400,
    ):
        self.db = _Db(dsn)
        self.max_pending, self.lease_seconds = max_pending, lease_seconds
        self.max_attempts, self.poll_interval = max_attempts, poll_interval
        self.retention_seconds = retention_seconds
        self._wake = asyncio.Event()
        self._last_purge = 0.0

    async def start(self):
        try:
            await self.db.execute("SELECT 1 FROM estado.updates LIMIT 1")
        except psycopg.Error:
            raise RuntimeError(
                "Não foi possível usar o estado durável. Verifique STATE_DATABASE_URL e execute "
                "`bi-db init-state`."
            ) from None
        await self.purge()

    async def close(self):
        await self.db.close()

    async def register(self, update_id, payload):
        rows = await self.db.execute(
            """INSERT INTO estado.updates (update_id, payload)
               SELECT %s, %s WHERE (SELECT count(*) FROM estado.updates
                                    WHERE status IN ('pendente', 'processando')) < %s
               ON CONFLICT (update_id) DO NOTHING RETURNING update_id""",
            (update_id, Jsonb(payload), self.max_pending),
        )
        if rows:
            self._wake.set()
            return RECEIVED
        exists = await self.db.execute(
            "SELECT 1 FROM estado.updates WHERE update_id = %s", (update_id,)
        )
        return DUPLICATE if exists else FULL

    async def claim(self):
        rows = await self.db.execute(
            """UPDATE estado.updates
               SET status = 'processando', tentativas = tentativas + 1,
                   reservado_ate = now() + make_interval(secs => %s)
               WHERE update_id = (
                   SELECT update_id FROM estado.updates
                   WHERE tentativas < %s AND (status = 'pendente'
                         OR (status = 'processando' AND reservado_ate < now()))
                   ORDER BY recebido_em, update_id FOR UPDATE SKIP LOCKED LIMIT 1)
               RETURNING update_id, payload""",
            (self.lease_seconds, self.max_attempts),
        )
        return (rows[0][0], rows[0][1]) if rows else None

    async def next(self):
        while True:
            self._wake.clear()
            try:
                item = await self.claim()
                if monotonic() - self._last_purge > 60:
                    await self.purge()
            except psycopg.Error:
                logger.error("falha_estado_duravel")
                item = None
                await asyncio.sleep(2)
            if item is not None:
                return item
            try:
                await asyncio.wait_for(self._wake.wait(), self.poll_interval)
            except TimeoutError:
                pass

    async def done(self, update_id):
        await self.db.execute(
            """UPDATE estado.updates SET status = 'concluido', payload = NULL,
               reservado_ate = NULL, concluido_em = now() WHERE update_id = %s""",
            (update_id,),
        )

    async def retry(self, update_id):
        await self.db.execute(
            """UPDATE estado.updates SET reservado_ate = NULL,
                 status = CASE WHEN tentativas >= %(max)s THEN 'falhou' ELSE 'pendente' END,
                 payload = CASE WHEN tentativas >= %(max)s THEN NULL ELSE payload END,
                 concluido_em = CASE WHEN tentativas >= %(max)s THEN now() END
               WHERE update_id = %(id)s""",
            {"max": self.max_attempts, "id": update_id},
        )
        self._wake.set()

    async def purge(self):
        self._last_purge = monotonic()
        await self.db.execute(
            """UPDATE estado.updates SET status = 'falhou', payload = NULL, concluido_em = now()
               WHERE status = 'processando' AND reservado_ate < now() AND tentativas >= %s""",
            (self.max_attempts,),
        )
        await self.db.execute(
            """DELETE FROM estado.updates
               WHERE concluido_em < now() - make_interval(secs => %s)""",
            (self.retention_seconds,),
        )

    async def join(self):
        while True:
            rows = await self.db.execute(
                "SELECT count(*) FROM estado.updates WHERE status IN ('pendente', 'processando')"
            )
            if rows[0][0] == 0:
                return
            await asyncio.sleep(self.poll_interval)


class PostgresSessionStore:
    def __init__(self, dsn, max_turns=8, ttl=3600, lock_timeout=60.0):
        self.dsn, self.max_turns, self.ttl, self.lock_timeout = dsn, max_turns, ttl, lock_timeout
        self._last_purge = 0.0

    def _open(self, chat_id, user_id):
        conn = psycopg.connect(self.dsn, autocommit=True, connect_timeout=5)
        try:
            if monotonic() - self._last_purge > 300:
                self._last_purge = monotonic()
                conn.execute(
                    "DELETE FROM estado.sessoes "
                    "WHERE atualizado_em < now() - make_interval(secs => %s)",
                    (self.ttl,),
                )
            conn.execute(
                "SELECT set_config('lock_timeout', %s, false)",
                (str(int(self.lock_timeout * 1000)),),
            )
            try:
                conn.execute(
                    "SELECT pg_advisory_lock(hashtextextended(%s, 0))", (f"{chat_id}:{user_id}",)
                )
            except psycopg.errors.LockNotAvailable:
                raise SessionsBusy(BUSY_MESSAGE) from None
            conn.execute("SELECT set_config('lock_timeout', '0', false)")
            row = conn.execute(
                """SELECT turnos, atualizado_em < now() - make_interval(secs => %s)
                   FROM estado.sessoes WHERE chat_id = %s AND user_id = %s""",
                (self.ttl, chat_id, user_id),
            ).fetchone()
        except BaseException:
            conn.close()
            raise
        return conn, ([] if row is None or row[1] else row[0])

    @staticmethod
    def _save(conn, chat_id, user_id, turns):
        conn.execute(
            """INSERT INTO estado.sessoes (chat_id, user_id, turnos) VALUES (%s, %s, %s)
               ON CONFLICT (chat_id, user_id)
               DO UPDATE SET turnos = EXCLUDED.turnos, atualizado_em = now()""",
            (chat_id, user_id, Jsonb(turns)),
        )

    @asynccontextmanager
    async def acquire(self, key):
        chat_id, user_id = key
        conn, turns = await asyncio.to_thread(self._open, chat_id, user_id)
        session = Session(deque(turns, maxlen=self.max_turns), monotonic())
        try:
            yield session
        finally:
            try:
                await asyncio.to_thread(self._save, conn, chat_id, user_id, list(session.turns))
            except psycopg.Error:
                logger.error("falha_estado_duravel")
            finally:
                await asyncio.to_thread(conn.close)
