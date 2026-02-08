from psycopg import AsyncConnection

from app.infrastructure.database.tables.users import UsersTable
from app.infrastructure.database.tables.downloads import DownloadsTable


class DB:
    def __init__(self, connection: AsyncConnection) -> None:
        self.users = UsersTable(connection)
        self.downloads = DownloadsTable(connection)
