from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import re
import os


#DATABASE_URL = "postgresql+asyncpg://postgres:12345678@localhost:5432/todo"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("No DATABASE URL ENV")


engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
