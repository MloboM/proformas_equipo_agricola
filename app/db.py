"""
Configuración de la base de datos SQLAlchemy
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

# Ruta de la base de datos
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "agriquote.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Configuración del engine
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Cambiar a True para debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa
Base = declarative_base()


@contextmanager
def get_db():
    """
    Context manager para obtener sesiones de base de datos
    Uso: with get_db() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Inicializa todas las tablas y configuración por defecto"""
    # Importar todos los modelos
    from app.models import (
        Customer, Advisor, Brand, Model, Configuration,
        Proforma, ProformaItem
    )
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    # Inicializar configuración por defecto
    from app.config_defaults import init_default_config
    with SessionLocal() as db:
        init_default_config(db)
        db.commit()


def reset_db():
    """
    CUIDADO: Elimina todas las tablas y las vuelve a crear
    Solo usar en desarrollo
    """
    Base.metadata.drop_all(bind=engine)
    init_db()