import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import re


#DATABASE_URL = "postgresql+asyncpg://postgres:12345678@localhost:5432/todo"

#raw_url = "postgresql+asyncpg://postgres:Tonyfiby16@db.wghpvhftdrrkfrnhzkfp.supabase.co:5432/postgres?sslmode=require"
#DATABASE_URL = re.sub(r"sslmode=require", "ssl=require", raw_url)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("No DATABASE URL ENV")

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"ssl": True},  
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
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
