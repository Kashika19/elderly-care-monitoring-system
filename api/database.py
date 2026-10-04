from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Use a local SQLite database by default and allow deployments/tests to override it.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eldercare.db")

# check_same_thread is needed for SQLite + multithreaded ASGI
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
