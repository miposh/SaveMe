import logging
from pathlib import Path

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "alembic" / "versions"


class DatabaseSchema:
    def __init__(self, connection: AsyncConnection) -> None:
        self._conn = connection

    async def create_tables(self) -> None:
        if not MIGRATIONS_DIR.exists():
            logger.warning("Migrations directory not found: %s", MIGRATIONS_DIR)
            return

        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for sql_file in sql_files:
            sql = sql_file.read_text(encoding="utf-8")
            logger.info("Applying migration: %s", sql_file.name)
            await self._conn.execute(sql)

        await self._conn.commit()
        logger.info("All migrations applied successfully")

    async def verify_tables(self) -> None:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        result = await self._conn.execute(query)
        rows = await result.fetchall()
        table_names = [row["table_name"] for row in rows]
        logger.info("Database tables: %s", table_names)
