from abc import ABC, abstractmethod
from typing import Any

from app.infrastructure.database.query.results import (
    MultipleQueryResult,
    SingleQueryResult,
)


class BaseConnection(ABC):
    @abstractmethod
    async def execute(
        self,
        sql: str,
        params: Any | None = None,
    ) -> int:
        pass

    @abstractmethod
    async def fetchone(
        self,
        sql: str,
        params: Any | None = None,
    ) -> SingleQueryResult:
        pass

    @abstractmethod
    async def fetchmany(
        self,
        sql: str,
        params: Any | None = None,
    ) -> MultipleQueryResult:
        pass

    @abstractmethod
    async def insert_and_fetchone(
        self,
        sql: str,
        params: Any,
    ) -> SingleQueryResult:
        pass

    @abstractmethod
    async def update_and_fetchone(
        self,
        sql: str,
        params: Any,
    ) -> SingleQueryResult:
        pass
