from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

#DATABASE_URL = "postgresql+asyncpg://postgres:12345678@localhost:5432/todo"
DATABASE_URL = ("postgresql+asyncpg://postgres:[YOUR_PASSWORD]@db.wghpvhftdrrkfrnhzkfp.supabase.co:5432/postgres?sslmode=require")

engine = create_async_engine(
    DATABASE_URL,
    echo=True
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
