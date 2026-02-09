from app.infrastructure.database.connection.base import BaseConnection
from app.infrastructure.database.tables.users import UsersTable
from app.infrastructure.database.tables.admins import AdminsTable
from app.infrastructure.database.tables.downloads import DownloadsTable
from app.infrastructure.database.tables.broadcasts import BroadcastsTable
from app.infrastructure.database.tables.video_cache import VideoCacheTable
from app.infrastructure.database.tables.statistics import StatisticsTable
from app.infrastructure.database.tables.rate_limits import RateLimitsTable


class DB:
    def __init__(self, connection: BaseConnection) -> None:
        self.connection = connection
        self.users = UsersTable(connection=connection)
        self.admins = AdminsTable(connection=connection)
        self.downloads = DownloadsTable(connection=connection)
        self.broadcasts = BroadcastsTable(connection=connection)
        self.video_cache = VideoCacheTable(connection=connection)
        self.statistics = StatisticsTable(connection=connection)
        self.rate_limits = RateLimitsTable(connection=connection)
