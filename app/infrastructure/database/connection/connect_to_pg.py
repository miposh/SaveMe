import logging
from urllib.parse import quote_plus

from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


async def get_pg_pool(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
    min_size: int = 1,
    max_size: int = 5,
) -> AsyncConnectionPool:
    encoded_password = quote_plus(password) if password else ""
    conninfo = (
        f"postgresql://{user}:{encoded_password}@{host}:{port}/{db_name}"
    )

    pool = AsyncConnectionPool(
        conninfo=conninfo,
        min_size=min_size,
        max_size=max_size,
        timeout=30.0,
        open=False,
        kwargs={"row_factory": dict_row},
    )

    await pool.open()

    async with pool.connection() as conn:
        version = await conn.execute("SELECT version()")
        row = await version.fetchone()
        if row:
            logger.info("PostgreSQL connected: %s", row["version"])

    return pool
