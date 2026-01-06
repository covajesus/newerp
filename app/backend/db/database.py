from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔵 Conexión a la base principal
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://admin:ChileSUR2026Admin!@intrajisbackend.com:3306/jisparking"
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size=20, max_overflow=0, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🟢 Conexión a otra base de datos (ej: jisparking)
SQLALCHEMY_DB2_URI = "mysql+pymysql://admin:Chile2025@jisbackend.com:3306/jisparking"
engine_db2 = create_engine(SQLALCHEMY_DB2_URI, pool_size=10, max_overflow=0, echo=False)
SessionLocalDB2 = sessionmaker(bind=engine_db2, autocommit=False, autoflush=False)
BaseDB2 = declarative_base()

def get_db2():
    db = SessionLocalDB2()
    try:
        yield db
    finally:
        db.close()