from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from config import DATABASE_URL

# Transaction pooler: no client-side pool, no prepared statements
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    connect_args={"prepare_threshold": None},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_conn():
    #One connection per request, inside a transaction.
    #Commits on success and rolls back if the request raises an error.
    with engine.begin() as conn:
        yield conn