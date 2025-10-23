"""
Modelos de datos completos para AgriQuote v2 - Con IVA personalizable y mejor manejo de errores
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, 
    DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db import Base


# ==================== CLIENTES ====================

class Customer(Base):
    """Modelo para clientes"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    company = Column(String(200), default="")
    email = Column(String(100), default="")
    phone = Column(String(50), default="")
    address = Column(Text, default="")
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    proformas = relationship("Proforma", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}')>"


# ==================== ASESORES ====================

class Advisor(Base):
    """Modelo para asesores de ventas"""
    __tablename__ = "advisors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(100), default="")
    phone = Column(String(50), default="")
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    proformas = relationship("Proforma", back_populates="advisor")
    
    def __repr__(self):
        return f"<Advisor(id={self.id}, name='{self.name}')>"


# ==================== MARCAS Y MODELOS ====================

class Brand(Base):
    """Modelo para marcas de equipos"""
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    equipment_type = Column(String(20), nullable=False)  # 'tractor' o 'implement'
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    models = relationship("Model", back_populates="brand", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Brand(id={self.id}, name='{self.name}', type='{self.equipment_type}')>"


class Model(Base):
    """Modelo para modelos de equipos"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, default="")  # Especificaciones técnicas
    base_price = Column(Float, default=0.0)
    image_path = Column(String(500), default="")
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    brand = relationship("Brand", back_populates="models")
    
    __table_args__ = (
        UniqueConstraint("brand_id", "name", name="uq_brand_model"),
    )
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', brand_id={self.brand_id})>"
    
    @property
    def full_name(self):
        """Nombre completo: Marca + Modelo"""
        return f"{self.brand.name} {self.name}"


# ==================== CONFIGURACIÓN ====================

class Configuration(Base):
    """Configuración general del sistema"""
    __tablename__ = "configuration"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    category = Column(String(50), default="general")  # general, tractor, implement, company, logos
    description = Column(String(200), default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Configuration(key='{self.key}', category='{self.category}')>"


# ==================== PROFORMAS ====================

class Proforma(Base):
    """Modelo para proformas/cotizaciones"""
    __tablename__ = "proformas"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Relaciones con otras tablas
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    advisor_id = Column(Integer, ForeignKey("advisors.id"), nullable=True, index=True)
    
    # Información adicional del cliente para esta proforma
    customer_attention = Column(String(200), default="")  # A la atención de
    
    # Tipo de proforma
    template = Column(String(20), nullable=False, index=True)  # 'tractor' o 'implement'
    
    # Detalles de la proforma
    validity_days = Column(Integer, default=15)
    date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Totales
    currency = Column(String(10), default="CRC")  # CRC, USD o MIXED
    subtotal = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)  # Descuento total
    subtotal_after_discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    # Notas personalizadas (sobrescriben configuración si se llenan)
    custom_terms = Column(Text, default="")
    custom_fiscal_note = Column(Text, default="")
    notes = Column(Text, default="")  # Notas adicionales
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pdf_path = Column(String(500), default="")
    
    # Relaciones
    customer = relationship("Customer", back_populates="proformas")
    advisor = relationship("Advisor", back_populates="proformas")
    items = relationship(
        "ProformaItem",
        back_populates="proforma",
        cascade="all, delete-orphan",
        order_by="ProformaItem.id"
    )
    
    def __repr__(self):
        return f"<Proforma(id={self.id}, number='{self.number}', customer_id={self.customer_id})>"
    
    def calculate_totals(self):
        """Calcula los totales basados en los items con IVA personalizable"""
        if not self.items:
            self.subtotal = self.discount = self.subtotal_after_discount = self.tax = self.total = 0.0
            return
        
        # Subtotal sin descuento
        self.subtotal = sum(item.line_subtotal for item in self.items)
        
        # Descuento total
        self.discount = sum(item.discount_amount for item in self.items)
        
        # Subtotal después de descuento
        self.subtotal_after_discount = self.subtotal - self.discount
        
        # IVA calculado individualmente por item con su tasa personalizada
        self.tax = sum(
            round((item.line_subtotal - item.discount_amount) * ((item.tax_rate or 13.0) / 100), 2)
            for item in self.items
        )
        
        # Total
        self.total = self.subtotal_after_discount + self.tax


# ==================== ITEMS DE PROFORMA ====================

class ProformaItem(Base):
    """Modelo para items de una proforma con IVA personalizable"""
    __tablename__ = "proforma_items"
    
    id = Column(Integer, primary_key=True, index=True)
    proforma_id = Column(
        Integer,
        ForeignKey("proformas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Referencia al modelo (opcional, puede ser null si se eliminó)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    
    # Datos congelados (snapshot del momento de la cotización)
    brand_name = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=True)  # Solo para tractores
    description = Column(Text, nullable=False, default="")
    image_path = Column(String(500), default="")
    
    # Cantidades y precios
    qty = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)  # Porcentaje de descuento
    discount_amount = Column(Float, default=0.0)  # Monto de descuento
    line_subtotal = Column(Float, nullable=False)  # qty * unit_price
    
    # IVA PERSONALIZABLE
    tax_rate = Column(Float, default=13.0)  # Tasa de IVA personalizable (por defecto 13%)
    line_tax = Column(Float, default=0.0)  # Monto de IVA para esta línea
    line_total = Column(Float, nullable=False)  # line_subtotal - discount_amount + line_tax
    
    currency = Column(String(10), nullable=False, default="CRC")
    
    # Relaciones
    proforma = relationship("Proforma", back_populates="items")
    
    def __repr__(self):
        return f"<ProformaItem(id={self.id}, brand='{self.brand_name}', model='{self.model_name}', tax={self.tax_rate}%)>"
    
    def calculate_totals(self):
        """Calcula los totales de la línea con IVA personalizable y manejo seguro de None"""
        self.line_subtotal = self.qty * self.unit_price
        self.discount_amount = round(self.line_subtotal * (self.discount_percent / 100), 2)
        subtotal_after_discount = self.line_subtotal - self.discount_amount
        
        # Asegurar que tax_rate no sea None y tenga un valor por defecto
        if self.tax_rate is None:
            self.tax_rate = 13.0
        
        self.line_tax = round(subtotal_after_discount * (self.tax_rate / 100), 2)
        self.line_total = subtotal_after_discount + self.line_tax