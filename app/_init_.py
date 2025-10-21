"""
Módulo principal de AgriQuote
Sistema de gestión y cotización de equipos agrícolas
"""

__version__ = "1.0.0"
__author__ = "AgriQuote Team"

from app.db import Base, engine, SessionLocal, init_db

# Inicializar base de datos al importar el módulo
init_db()