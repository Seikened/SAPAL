from pathlib import Path
from sqlmodel import SQLModel
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Carpeta del paquete backend (donde vive este db.py)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"
print(f"[DEBUG] Database path: {DB_PATH}")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

ASYNC_ENGINE = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=ASYNC_ENGINE, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with ASYNC_ENGINE.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@event.listens_for(ASYNC_ENGINE.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

async def get_session():
    async with SessionLocal() as session:
        yield session