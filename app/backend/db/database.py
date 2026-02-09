from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# 🔵 Conexión a la base principal
# Obtener credenciales desde variables de entorno
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_NAME = os.getenv('DB_NAME', 'jisparking')
if not DB_USER or not DB_PASSWORD:
    raise ValueError(
        "DB_USER y DB_PASSWORD no encontrados en variables de entorno. "
        "Por favor, crea un archivo .env con estas variables definidas."
    )

# Codificar la contraseña para que funcione correctamente en la URI (maneja caracteres especiales)
DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size=20, max_overflow=0, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🟢 Conexión a otra base de datos (DB2)
# Obtener credenciales desde variables de entorno para DB2
DB2_USER = os.getenv('DB2_USER')
DB2_PASSWORD = os.getenv('DB2_PASSWORD')
DB2_HOST = os.getenv('DB2_HOST')
DB2_PORT = os.getenv('DB2_PORT', '3306')
DB2_NAME = os.getenv('DB2_NAME', 'jisparking')

# DB2 es opcional, solo se inicializa si las credenciales están disponibles
if DB2_USER and DB2_PASSWORD and DB2_HOST:
    # Codificar la contraseña para que funcione correctamente en la URI
    DB2_PASSWORD_ENCODED = quote_plus(DB2_PASSWORD)
    SQLALCHEMY_DB2_URI = f"mysql+pymysql://{DB2_USER}:{DB2_PASSWORD_ENCODED}@{DB2_HOST}:{DB2_PORT}/{DB2_NAME}"
    engine_db2 = create_engine(SQLALCHEMY_DB2_URI, pool_size=10, max_overflow=0, echo=False)
    SessionLocalDB2 = sessionmaker(bind=engine_db2, autocommit=False, autoflush=False)
    BaseDB2 = declarative_base()
else:
    # Si no hay credenciales para DB2, establecer valores None
    engine_db2 = None
    SessionLocalDB2 = None
    BaseDB2 = None

def get_db2():
    if SessionLocalDB2 is None:
        raise RuntimeError(
            "DB2 no está configurado. Por favor, proporciona DB2_USER, DB2_PASSWORD y DB2_HOST "
            "en el archivo .env si necesitas usar esta conexión."
        )
    db = SessionLocalDB2()
    try:
        yield db
    finally:
        db.close()