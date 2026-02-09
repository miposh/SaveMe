import logging
from urllib.parse import quote

from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


def build_pg_conninfo(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
) -> str:
    conninfo = (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}"
        f"@{host}:{port}/{db_name}"
    )
    logger.debug(
        "Building PostgreSQL connection string (password omitted): "
        "postgresql://%s@%s:%s/%s",
        quote(user, safe=""), host, port, db_name,
    )
    return conninfo


async def get_pg_pool(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
    min_size: int = 1,
    max_size: int = 10,
    timeout: float | None = 30.0,
) -> AsyncConnectionPool:
    conninfo = build_pg_conninfo(db_name, host, port, user, password)

    try:
        db_pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=min_size,
            max_size=max_size,
            timeout=timeout,
            open=False,
            kwargs={"row_factory": dict_row},
        )

        await db_pool.open()

        async with db_pool.connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT version();")
                db_version = await cursor.fetchone()
                if db_version:
                    version = db_version.get("version") or next(iter(db_version.values()), None)
                    logger.info("Connected to PostgreSQL: %s", version)

        return db_pool
    except Exception as e:
        logger.exception("Failed to initialize PostgreSQL pool: %s", e)
        raise
