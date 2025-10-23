"""
Operaciones CRUD completas para AgriQuote v2 - Con soporte para IVA personalizable y búsqueda avanzada
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func
from datetime import datetime

from app.models import (
    Customer, Advisor, Brand, Model, Configuration,
    Proforma, ProformaItem
)


# ==================== CLIENTES ====================

def list_customers(
    db: Session,
    active_only: bool = True,
    search: Optional[str] = None
) -> List[Customer]:
    """Lista clientes con filtros"""
    query = select(Customer)
    
    if active_only:
        query = query.where(Customer.active == True)
    
    if search:
        search_filter = or_(
            Customer.name.ilike(f"%{search}%"),
            Customer.company.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    query = query.order_by(Customer.name)
    return db.scalars(query).all()


def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    """Obtiene un cliente por ID"""
    return db.get(Customer, customer_id)


def create_customer(
    db: Session,
    name: str,
    company: str = "",
    email: str = "",
    phone: str = "",
    address: str = "",
    active: bool = True
) -> Customer:
    """Crea un nuevo cliente"""
    customer = Customer(
        name=name.strip(),
        company=company.strip(),
        email=email.strip(),
        phone=phone.strip(),
        address=address.strip(),
        active=active
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(
    db: Session,
    customer_id: int,
    **kwargs
) -> Optional[Customer]:
    """Actualiza un cliente"""
    customer = db.get(Customer, customer_id)
    if not customer:
        return None
    
    for key, value in kwargs.items():
        if value is not None and hasattr(customer, key):
            if isinstance(value, str):
                setattr(customer, key, value.strip())
            else:
                setattr(customer, key, value)
    
    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> bool:
    """Elimina un cliente"""
    customer = db.get(Customer, customer_id)
    if not customer:
        return False
    db.delete(customer)
    db.commit()
    return True


# ==================== ASESORES ====================

def list_advisors(
    db: Session,
    active_only: bool = True,
    search: Optional[str] = None
) -> List[Advisor]:
    """Lista asesores con filtros"""
    query = select(Advisor)
    
    if active_only:
        query = query.where(Advisor.active == True)
    
    if search:
        search_filter = or_(
            Advisor.name.ilike(f"%{search}%"),
            Advisor.email.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    query = query.order_by(Advisor.name)
    return db.scalars(query).all()


def get_advisor(db: Session, advisor_id: int) -> Optional[Advisor]:
    """Obtiene un asesor por ID"""
    return db.get(Advisor, advisor_id)


def create_advisor(
    db: Session,
    name: str,
    email: str = "",
    phone: str = "",
    active: bool = True
) -> Advisor:
    """Crea un nuevo asesor"""
    advisor = Advisor(
        name=name.strip(),
        email=email.strip(),
        phone=phone.strip(),
        active=active
    )
    db.add(advisor)
    db.commit()
    db.refresh(advisor)
    return advisor


def update_advisor(
    db: Session,
    advisor_id: int,
    **kwargs
) -> Optional[Advisor]:
    """Actualiza un asesor"""
    advisor = db.get(Advisor, advisor_id)
    if not advisor:
        return None
    
    for key, value in kwargs.items():
        if value is not None and hasattr(advisor, key):
            if isinstance(value, str):
                setattr(advisor, key, value.strip())
            else:
                setattr(advisor, key, value)
    
    advisor.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(advisor)
    return advisor


def delete_advisor(db: Session, advisor_id: int) -> bool:
    """Elimina un asesor"""
    advisor = db.get(Advisor, advisor_id)
    if not advisor:
        return False
    db.delete(advisor)
    db.commit()
    return True


# ==================== MARCAS ====================

def list_brands(
    db: Session,
    equipment_type: Optional[str] = None,
    active_only: bool = True
) -> List[Brand]:
    """Lista marcas con filtros"""
    query = select(Brand)
    
    if active_only:
        query = query.where(Brand.active == True)
    
    if equipment_type:
        query = query.where(Brand.equipment_type == equipment_type)
    
    query = query.order_by(Brand.name)
    return db.scalars(query).all()


def get_brand(db: Session, brand_id: int) -> Optional[Brand]:
    """Obtiene una marca por ID"""
    return db.get(Brand, brand_id)


def create_brand(
    db: Session,
    name: str,
    equipment_type: str,
    active: bool = True
) -> Brand:
    """Crea una nueva marca"""
    brand = Brand(
        name=name.strip(),
        equipment_type=equipment_type,
        active=active
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def update_brand(
    db: Session,
    brand_id: int,
    **kwargs
) -> Optional[Brand]:
    """Actualiza una marca"""
    brand = db.get(Brand, brand_id)
    if not brand:
        return None
    
    for key, value in kwargs.items():
        if value is not None and hasattr(brand, key):
            if isinstance(value, str):
                setattr(brand, key, value.strip())
            else:
                setattr(brand, key, value)
    
    brand.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(brand)
    return brand


def delete_brand(db: Session, brand_id: int) -> bool:
    """Elimina una marca y sus modelos"""
    brand = db.get(Brand, brand_id)
    if not brand:
        return False
    db.delete(brand)
    db.commit()
    return True


# ==================== MODELOS ====================

def list_models(
    db: Session,
    brand_id: Optional[int] = None,
    equipment_type: Optional[str] = None,
    active_only: bool = True
) -> List[Model]:
    """Lista modelos con filtros"""
    query = select(Model).join(Brand)
    
    if active_only:
        query = query.where(Model.active == True)
    
    if brand_id:
        query = query.where(Model.brand_id == brand_id)
    
    if equipment_type:
        query = query.where(Brand.equipment_type == equipment_type)
    
    query = query.order_by(Brand.name, Model.name)
    return db.scalars(query).all()


def get_model(db: Session, model_id: int) -> Optional[Model]:
    """Obtiene un modelo por ID"""
    return db.get(Model, model_id)


def create_model(
    db: Session,
    brand_id: int,
    name: str,
    description: str = "",
    base_price: float = 0.0,
    image_path: str = "",
    active: bool = True
) -> Model:
    """Crea un nuevo modelo"""
    model = Model(
        brand_id=brand_id,
        name=name.strip(),
        description=description.strip(),
        base_price=base_price,
        image_path=image_path,
        active=active
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_model(
    db: Session,
    model_id: int,
    **kwargs
) -> Optional[Model]:
    """Actualiza un modelo"""
    model = db.get(Model, model_id)
    if not model:
        return None
    
    for key, value in kwargs.items():
        if value is not None and hasattr(model, key):
            if isinstance(value, str):
                setattr(model, key, value.strip())
            else:
                setattr(model, key, value)
    
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model_id: int) -> bool:
    """Elimina un modelo"""
    model = db.get(Model, model_id)
    if not model:
        return False
    db.delete(model)
    db.commit()
    return True


# ==================== CONFIGURACIÓN ====================

def get_config(db: Session, key: str, default: str = "") -> str:
    """Obtiene un valor de configuración"""
    config = db.scalars(
        select(Configuration).where(Configuration.key == key)
    ).first()
    return config.value if config else default


def set_config(
    db: Session,
    key: str,
    value: str,
    category: str = "general",
    description: str = ""
) -> Configuration:
    """Establece un valor de configuración"""
    config = db.scalars(
        select(Configuration).where(Configuration.key == key)
    ).first()
    
    if config:
        config.value = value
        config.updated_at = datetime.utcnow()
    else:
        config = Configuration(
            key=key,
            value=value,
            category=category,
            description=description
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    return config


def get_all_config(db: Session, category: Optional[str] = None) -> Dict[str, str]:
    """Obtiene todas las configuraciones como diccionario"""
    query = select(Configuration)
    if category:
        query = query.where(Configuration.category == category)
    
    configs = db.scalars(query).all()
    return {c.key: c.value for c in configs}


# ==================== PROFORMAS ====================

def list_proformas(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    customer_id: Optional[int] = None,
    template: Optional[str] = None
) -> List[Proforma]:
    """Lista proformas con filtros básicos (SOLO para carga inicial)"""
    query = select(Proforma).order_by(Proforma.created_at.desc())
    
    if customer_id:
        query = query.where(Proforma.customer_id == customer_id)
    
    if template:
        query = query.where(Proforma.template == template)
    
    query = query.limit(limit).offset(offset)
    return db.scalars(query).all()


def search_proformas(
    db: Session,
    customer_search: Optional[str] = None,
    model_search: Optional[str] = None,
    proforma_number: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    advisor_id: Optional[int] = None,
    template: Optional[str] = None,
    limit: int = 1000
) -> List[Proforma]:
    """Búsqueda avanzada de proformas con filtros múltiples incluyendo número de proforma"""
    
    # Construir query base
    query = select(Proforma).join(Customer).order_by(Proforma.created_at.desc())
    
    # Filtro por número de proforma (búsqueda parcial)
    if proforma_number:
        query = query.where(Proforma.number.ilike(f"%{proforma_number}%"))
    
    # Filtro por cliente (nombre o empresa)
    if customer_search:
        customer_filter = or_(
            Customer.name.ilike(f"%{customer_search}%"),
            Customer.company.ilike(f"%{customer_search}%")
        )
        query = query.where(customer_filter)
    
    # Filtro por fechas
    if date_from:
        query = query.where(Proforma.date >= date_from)
    if date_to:
        # Agregar 23:59:59 al final del día para incluir todo el día
        date_to_end = date_to.replace(hour=23, minute=59, second=59)
        query = query.where(Proforma.date <= date_to_end)
    
    # Filtro por asesor
    if advisor_id:
        query = query.where(Proforma.advisor_id == advisor_id)
    
    # Filtro por tipo de template
    if template:
        query = query.where(Proforma.template == template)
    
    query = query.limit(limit)
    proformas = db.scalars(query).all()
    
    # Filtro por modelo (requiere búsqueda en items)
    if model_search and proformas:
        filtered_proformas = []
        for proforma in proformas:
            for item in proforma.items:
                if (model_search.lower() in item.model_name.lower() or 
                    model_search.lower() in item.brand_name.lower()):
                    filtered_proformas.append(proforma)
                    break
        return filtered_proformas
    
    return proformas


def get_proforma(db: Session, proforma_id: int) -> Optional[Proforma]:
    """Obtiene una proforma por ID"""
    return db.get(Proforma, proforma_id)


def get_proforma_by_number(db: Session, number: str) -> Optional[Proforma]:
    """Obtiene una proforma por número"""
    return db.scalars(
        select(Proforma).where(Proforma.number == number)
    ).first()


def duplicate_proforma(
    db: Session,
    original_id: int,
    new_number: str,
    new_date: Optional[datetime] = None
) -> Optional[Proforma]:
    """Duplica una proforma existente con nuevo número y fecha"""
    original = db.get(Proforma, original_id)
    if not original:
        return None
    
    # Preparar datos de items manteniendo toda la información
    items_data = []
    for item in original.items:
        items_data.append({
            "model_id": item.model_id,
            "brand_name": item.brand_name,
            "model_name": item.model_name,
            "year": item.year,
            "description": item.description,
            "image_path": item.image_path,
            "qty": item.qty,
            "unit_price": item.unit_price,
            "discount_percent": item.discount_percent,
            "currency": item.currency,
            "tax_rate": item.tax_rate  # Mantener IVA personalizado
        })
    
    # Crear nueva proforma con los mismos datos
    new_proforma = create_proforma(
        db,
        number=new_number,
        customer_id=original.customer_id,
        template=original.template,
        items_data=items_data,
        advisor_id=original.advisor_id,
        customer_attention=original.customer_attention,
        validity_days=original.validity_days,
        date=new_date or datetime.utcnow(),
        custom_terms=original.custom_terms,
        custom_fiscal_note=original.custom_fiscal_note,
        notes=original.notes
    )
    
    return new_proforma


def create_proforma(
    db: Session,
    number: str,
    customer_id: int,
    template: str,
    items_data: List[dict],
    advisor_id: Optional[int] = None,
    customer_attention: str = "",
    validity_days: int = 15,
    date: Optional[datetime] = None,
    custom_terms: str = "",
    custom_fiscal_note: str = "",
    notes: str = ""
) -> Proforma:
    """Crea una nueva proforma con sus items (con IVA personalizable)"""
    
    # Crear la proforma
    proforma = Proforma(
        number=number,
        customer_id=customer_id,
        advisor_id=advisor_id,
        customer_attention=customer_attention.strip(),
        template=template,
        validity_days=validity_days,
        date=date or datetime.utcnow(),
        custom_terms=custom_terms.strip(),
        custom_fiscal_note=custom_fiscal_note.strip(),
        notes=notes.strip()
    )
    
    db.add(proforma)
    db.flush()
    
    # Crear los items con IVA personalizable
    currencies = set()
    for item_data in items_data:
        item = ProformaItem(
            proforma_id=proforma.id,
            model_id=item_data.get("model_id"),
            brand_name=item_data["brand_name"],
            model_name=item_data["model_name"],
            year=item_data.get("year"),
            description=item_data.get("description", ""),
            image_path=item_data.get("image_path", ""),
            qty=item_data["qty"],
            unit_price=item_data["unit_price"],
            discount_percent=item_data.get("discount_percent", 0.0),
            currency=item_data["currency"],
            # IVA personalizable - usar el valor proporcionado o 13% por defecto
            tax_rate=item_data.get("tax_rate", 13.0)
        )
        item.calculate_totals()
        currencies.add(item_data["currency"])
        db.add(item)
    
    # Determinar moneda
    proforma.currency = "MIXED" if len(currencies) > 1 else currencies.pop()
    
    # Calcular totales
    db.flush()
    proforma.calculate_totals()
    
    db.commit()
    db.refresh(proforma)
    return proforma


def delete_proforma(db: Session, proforma_id: int) -> bool:
    """Elimina una proforma y sus items asociados"""
    proforma = db.get(Proforma, proforma_id)
    if not proforma:
        return False
    db.delete(proforma)
    db.commit()
    return True


# ==================== ESTADÍSTICAS ====================

def get_stats(db: Session) -> Dict:
    """Obtiene estadísticas generales del sistema"""
    try:
        total_customers = db.scalar(select(func.count(Customer.id))) or 0
        active_customers = db.scalar(
            select(func.count(Customer.id)).where(Customer.active == True)
        ) or 0
        total_advisors = db.scalar(select(func.count(Advisor.id))) or 0
        total_brands = db.scalar(select(func.count(Brand.id))) or 0
        total_models = db.scalar(select(func.count(Model.id))) or 0
        total_proformas = db.scalar(select(func.count(Proforma.id))) or 0
        
        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_advisors": total_advisors,
            "total_brands": total_brands,
            "total_models": total_models,
            "total_proformas": total_proformas,
        }
    except Exception as e:
        # Si hay algún error, retornar valores por defecto
        print(f"Error en get_stats: {e}")
        return {
            "total_customers": 0,
            "active_customers": 0,
            "total_advisors": 0,
            "total_brands": 0,
            "total_models": 0,
            "total_proformas": 0,
        }