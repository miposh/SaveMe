import logging
from pathlib import Path

from app.infrastructure.database.connection.base import BaseConnection

logger = logging.getLogger(__name__)


class DatabaseSchema:
    SQL_DIR = Path(__file__).parent.parent.parent.parent / "migrations"

    MIGRATIONS_TO_APPLY = [
        "001_create_users_table.sql",
        "002_create_admins_table.sql",
        "003_create_downloads_table.sql",
        "004_create_rate_limits_table.sql",
        "005_create_statistics_table.sql",
        "006_create_broadcasts_table.sql",
        "007_create_video_cache_table.sql",
        "008_reconcile_schema.sql",
    ]

    def __init__(self, connection: BaseConnection) -> None:
        self.connection = connection

    async def create_tables(self) -> None:
        logger.info("Starting database schema initialization...")

        for sql_file in self.MIGRATIONS_TO_APPLY:
            file_path = self.SQL_DIR / sql_file

            if not file_path.exists():
                logger.warning("SQL file not found: %s", file_path)
                continue

            try:
                sql_content = file_path.read_text(encoding="utf-8")
                await self.connection.execute(sql=sql_content)
                logger.info("Executed: %s", sql_file)
            except Exception as e:
                logger.error("Failed to execute %s: %s", sql_file, e)
                raise

        logger.info("Database schema initialization completed")

    async def verify_tables(self) -> bool:
        required_tables = ["users", "admins", "downloads", "video_cache"]

        try:
            result = await self.connection.fetchone(
                sql="""
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = ANY(%s)
                """,
                params=(required_tables,),
            )

            count = result.data.get("count", 0) if result.data else 0

            if count == len(required_tables):
                logger.info("All %d required tables exist", count)
                return True

            logger.warning("Only %d/%d tables exist", count, len(required_tables))
            return False

        except Exception as e:
            logger.error("Failed to verify tables: %s", e)
            return False
