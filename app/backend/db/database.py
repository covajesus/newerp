from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://admin:Chile20255!@jisbackend.com:3306/jisparking"

# Crear el motor con echo=True para activar el registro de consultas
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size=20, max_overflow=0, echo=False)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

