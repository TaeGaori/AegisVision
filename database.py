import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:1234@localhost:5432/AegisVision')

engine = create_engine(DATABASE_URL)
Sessionmaker = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = sessionmaker()
    try:
        yield db
    finally:
        db.close()