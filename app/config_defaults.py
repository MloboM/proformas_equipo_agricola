"""
Valores por defecto de configuración para AgriQuote
"""

# Límites de caracteres para secciones fijas
MAX_CHARS = {
    "company_name": 60,
    "company_address": 150,
    "company_phone": 30,
    "company_email": 50,
    "company_web": 50,
    "advisor_name": 60,
    "advisor_email": 50,
    "advisor_phone": 30,
    "terms_tractor": 800,
    "terms_implement": 800,
    "fiscal_note": 400,
    "customer_name": 80,
    "customer_company": 80,
    "customer_attention": 80,
    "product_description": 1000,
}

# Configuraciones por defecto
DEFAULT_CONFIG = {
    # Datos de la empresa
    "company_name": "Colono",
    "company_address": "Limón, Pococí, Guápiles",
    "company_phone": "+506 2799-6120",
    "company_email": "ventas@colono.cr",
    "company_web": "www.colono.cr",
    
    # Términos y condiciones - Tractores
    "terms_tractor": """Incluye:
1. El lugar de entrega es en las instalaciones del comprador en el territorio costarricense, sin costo.
2. El período de garantía es de Doce (12) meses sin límite de hora a partir de la fecha de entrega. Esta Garantía es ante defectos de fabricación o cualquier anomalía debido a inconvenientes de manufactura y/o materias primas que afecten el funcionamiento normal del equipo.
3. Gastos de inscripción y placas metálicas.
4. Tiempo de Entrega: A convenir con el cliente.
5. Entrega técnica.""",
    
    # Términos y condiciones - Implementos
    "terms_implement": """Incluye:
1. El lugar de entrega es en las instalaciones del comprador en el territorio costarricense, sin costo.
2. Capacitación de operadores.
3. El período de garantía es de seis (6) meses sobre el equipo.""",
    
    # Nota fiscal
    "fiscal_note": """Al estar registrado ante la autoridad tributaria como productor de productos e insumos agropecuarios, podrá gestionar la exoneración del IVA a través del departamento correspondiente del Ministerio de Hacienda.""",
}

# Descripciones de configuración
CONFIG_DESCRIPTIONS = {
    "company_name": "Nombre de la empresa",
    "company_address": "Dirección física de la empresa",
    "company_phone": "Teléfono de contacto",
    "company_email": "Correo electrónico principal",
    "company_web": "Sitio web",
    "terms_tractor": "Términos y condiciones para tractores",
    "terms_implement": "Términos y condiciones para implementos",
    "fiscal_note": "Nota fiscal sobre exoneración de IVA",
}

# Categorías de configuración
CONFIG_CATEGORIES = {
    "company_name": "company",
    "company_address": "company",
    "company_phone": "company",
    "company_email": "company",
    "company_web": "company",
    "terms_tractor": "tractor",
    "terms_implement": "implement",
    "fiscal_note": "general",
}


def init_default_config(db):
    """
    Inicializa la configuración por defecto si no existe
    NOTA: Se importan las funciones aquí para evitar importación circular
    """
    # Importación local para evitar circularidad
    from sqlalchemy import select
    from app.models import Configuration
    from datetime import datetime
    
    for key, default_value in DEFAULT_CONFIG.items():
        # Verificar si existe
        config = db.scalars(
            select(Configuration).where(Configuration.key == key)
        ).first()
        
        if not config:
            # Crear nueva configuración
            category = CONFIG_CATEGORIES.get(key, "general")
            description = CONFIG_DESCRIPTIONS.get(key, "")
            
            new_config = Configuration(
                key=key,
                value=default_value,
                category=category,
                description=description
            )
            db.add(new_config)
    
    # Commitear todos los cambios al final
    db.commit()


def validate_char_limit(key: str, value: str) -> tuple[bool, str]:
    """
    Valida que un valor no exceda el límite de caracteres
    Retorna (es_válido, mensaje)
    """
    if key not in MAX_CHARS:
        return True, ""
    
    max_length = MAX_CHARS[key]
    current_length = len(value)
    
    if current_length > max_length:
        return False, f"El texto excede el límite de {max_length} caracteres ({current_length}/{max_length})"
    
    return True, f"{current_length}/{max_length} caracteres"