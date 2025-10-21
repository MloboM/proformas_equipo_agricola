"""
Modelo para almacenar términos y condiciones por plantilla
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from app.db import Base


class Terms(Base):
    """
    Almacena términos y condiciones personalizados por tipo de plantilla
    """
    __tablename__ = "terms"
    
    id = Column(Integer, primary_key=True, index=True)
    template = Column(String(20), nullable=False)  # 'tractor' o 'implement'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("template", name="uq_terms_template"),
    )
    
    def __repr__(self):
        return f"<Terms(template='{self.template}')>"
