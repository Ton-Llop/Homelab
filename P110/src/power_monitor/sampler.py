import asyncio
import logging
from datetime import datetime, timedelta

from .models import PowerSnapshot
from .storage import SampleStore
from .tapo import TapoPowerReader

logger = logging.getLogger(__name__)


class PowerSampler:
    """Sondea el enchufe en bucle y guarda el historico.

    Es el unico que habla con el P110: /power sirve lo que este bucle ha dejado
    en memoria, asi que el enchufe recibe siempre el mismo trafico haya una
    pestana de Homarr abierta o diez.
    """

    def __init__(
        self,
        reader: TapoPowerReader,
        store: SampleStore,
        poll_seconds: int,
        store_seconds: int,
        on_threshold_w: float,
    ) -> None:
        self._reader = reader
        self._store = store
        self._poll_seconds = poll_seconds
        self._store_seconds = store_seconds
        self._on_threshold_w = on_threshold_w

        self.snapshot: PowerSnapshot | None = None
        self.updated_at: datetime | None = None
        self.year_runtime_min: int | None = None
        self.measuring_since: datetime | None = None
        self._stored_at: datetime | None = None

    @property
    def is_fresh(self) -> bool:
        if self.snapshot is None or self.updated_at is None:
            return False

        age = (datetime.now() - self.updated_at).total_seconds()
        return age < self._poll_seconds * 3

    async def run(self) -> None:
        await self._refresh_year()

        while True:
            await self._tick()
            await asyncio.sleep(self._poll_seconds)

    async def _tick(self) -> None:
        try:
            snapshot = await self._reader.read()
        except Exception as exc:

            logger.warning("Muestreo fallido: %s", exc)
            return

        now = datetime.now()
        self.snapshot = snapshot
        self.updated_at = now

        if self._stored_at is not None:
            pending = (now - self._stored_at).total_seconds() < self._store_seconds
            if pending:
                return

        await asyncio.to_thread(self._store.record, now, snapshot.power_w)
        self._stored_at = now
        await self._refresh_year()

    async def _refresh_year(self) -> None:
        start_of_year = datetime(datetime.now().year, 1, 1)

        self.year_runtime_min = await asyncio.to_thread(
            self._store.minutes_above, start_of_year, self._on_threshold_w
        )
        self.measuring_since = await asyncio.to_thread(self._store.first_sample_at)

    async def prune(self, retention_days: int) -> None:
        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted = await asyncio.to_thread(self._store.delete_before, cutoff)

        if deleted:
            logger.info("Historico: %d muestras anteriores a %s eliminadas", deleted, cutoff.date())
