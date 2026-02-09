import logging

from app.infrastructure.database.connection.base import BaseConnection

logger = logging.getLogger(__name__)


class BaseTable:
    def __init__(self, connection: BaseConnection) -> None:
        self._connection = connection
