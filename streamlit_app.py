# --- FIX sys.path ---
from pathlib import Path as _P
from pathlib import Path  # Import directo
import sys as _sys
_ROOT = _P(__file__).resolve().parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))
# ---------------------

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

import streamlit as st

# Imports del proyecto
from app.db import SessionLocal, init_db
from app import crud
from app.pdf import build_proforma_pdf
from app.config_defaults import MAX_CHARS, validate_char_limit

# Inicializar base de datos
init_db()

# Configuración de directorios
MEDIA_DIR = _ROOT / "media"
UPLOAD_DIR = MEDIA_DIR / "uploads"
LOGOS_DIR = MEDIA_DIR / "logos"
OUTPUTS_DIR = _ROOT / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de página
st.set_page_config(
    page_title="AgriQuote - Sistema de Cotizaciones",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (con tamaño de fuente reducido para métricas)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #388E3C;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #66BB6A;
        padding-bottom: 0.5rem;
    }
    .stButton>button {
        background-color: #2E7D32;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
    }
    .char-counter {
        font-size: 0.85rem;
        color: #666;
        text-align: right;
        margin-top: -10px;
    }
    .char-counter.warning {
        color: #FF9800;
    }
    .char-counter.error {
        color: #F44336;
    }
    /* Reducir tamaño de fuente de métricas en totales */
    .metric-container {
        font-size: 0.9rem !important;
    }
    .metric-container [data-testid="metric-container"] {
        font-size: 0.9rem !important;
    }
    .metric-container .metric-label {
        font-size: 0.85rem !important;
    }
    .metric-container .metric-value {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    /* Estilo para ventana modal */
    .modal-dialog {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        border: 1px solid #ddd;
        margin: 20px auto;
        max-width: 500px;
    }
    .modal-success {
        background-color: #E8F5E8;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# ========================= UTILIDADES =========================

def format_currency(amount: float, currency: str = "CRC") -> str:
    """Formatea montos con símbolo de moneda"""
    symbol = "₡" if currency == "CRC" else "$"
    return f"{symbol}{amount:,.2f}"


def save_uploaded_image(file, prefix: str = "img") -> str:
    """Guarda imagen subida y retorna la ruta"""
    if not file:
        return ""
    
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return ""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}{ext}"
    filepath = UPLOAD_DIR / filename
    
    with open(filepath, "wb") as f:
        f.write(file.getbuffer())
    
    return str(filepath)


def validate_email(email: str) -> bool:
    """Validación básica de email"""
    if not email:
        return True
    return "@" in email and "." in email.split("@")[1]


def generate_proforma_number() -> str:
    """Genera número único de proforma"""
    return f"PF-{datetime.now():%Y%m%d-%H%M%S}"


def show_char_counter(key: str, current_length: int):
    """Muestra contador de caracteres"""
    if key not in MAX_CHARS:
        return
    
    max_length = MAX_CHARS[key]
    percentage = (current_length / max_length) * 100
    
    css_class = "char-counter"
    if percentage > 90:
        css_class += " error"
    elif percentage > 75:
        css_class += " warning"
    
    st.markdown(
        f'<div class="{css_class}">{current_length}/{max_length} caracteres</div>',
        unsafe_allow_html=True
    )


def show_duplicate_modal(original_number: str, new_number: str):
    """Muestra modal de confirmación de duplicación con botón de acción"""
    modal_html = f"""
    <div class="modal-dialog">
        <div class="modal-success">
            <h3 style="color: #4CAF50; margin: 0 0 10px 0;">✅ Proforma Duplicada</h3>
            <p style="margin: 5px 0;">Se ha creado una copia de la proforma <strong>{original_number}</strong></p>
            <p style="margin: 5px 0;">Nueva proforma generada: <strong>{new_number}</strong></p>
            <p style="margin: 10px 0 0 0; font-size: 0.9rem; color: #666;">
                Usa el botón de abajo para ir a la nueva proforma
            </p>
        </div>
    </div>
    """
    st.markdown(modal_html, unsafe_allow_html=True)


# ========================= SIDEBAR =========================

with st.sidebar:
    if (LOGOS_DIR / "colono.png").exists():
        st.image(str(LOGOS_DIR / "colono.png"), width=200)
    
    st.markdown("---")
    
    # Verificar si hay redirección pendiente por duplicación
    if st.session_state.get('redirect_to_new_proforma', False):
        # Limpiar flag y forzar selección de Nueva Proforma
        st.session_state.redirect_to_new_proforma = False
        default_index = 2  # Índice de "Nueva Proforma"
    else:
        default_index = 0  # Índice por defecto
    
    # Menú principal
    menu_option = st.radio(
        "Navegación",
        [
            "🏠 Inicio",
            "📊 Ver Proformas", 
            "📄 Nueva Proforma",
            "📋 Mantenimientos",
            "⚙️ Configuración"
        ],
        index=default_index
    )
    
    # RESET de búsqueda al salir de "Ver Proformas"
    if menu_option != "📊 Ver Proformas" and st.session_state.get('current_menu') == "📊 Ver Proformas":
        # El usuario salió de Ver Proformas, resetear búsqueda
        st.session_state.search_performed = False
        st.session_state.search_results = []
        st.session_state.show_duplicate_dialog = False
        st.session_state.show_delete_dialog = False
    
    # Guardar menú actual para detectar cambios
    st.session_state.current_menu = menu_option
    
    # Submenú para Mantenimientos
    submenu = None
    if menu_option == "📋 Mantenimientos":
        submenu = st.radio(
            "Sección",
            ["👥 Clientes", "👔 Asesores", "🏭 Marcas", "📦 Modelos"]
        )


# ========================= PÁGINA PRINCIPAL =========================

if menu_option == "🏠 Inicio":
    st.markdown('<p class="main-header">🚜 AgriQuote - Sistema de Cotizaciones</p>', unsafe_allow_html=True)
    
    st.markdown("### 📊 Estadísticas")
    
    with SessionLocal() as db:
        stats = crud.get_stats(db)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**👥 Clientes**")
        st.metric("Total registrados", stats["total_customers"])
        st.metric("Activos", stats["active_customers"])
    
    with col2:
        st.success("**📦 Catálogo**")
        st.metric("Marcas", stats["total_brands"])
        st.metric("Modelos", stats["total_models"])
    
    with col3:
        st.warning("**📋 Proformas**")
        st.metric("Total generadas", stats["total_proformas"])
    
    st.markdown("---")
    st.markdown("### 🚀 Inicio Rápido")
    
    st.markdown("""
    **Bienvenido al sistema AgriQuote.** Aquí puedes:
    
    1. **Crear cotizaciones:** Genera proformas profesionales para tractores e implementos
    2. **Gestionar catálogo:** Administra marcas, modelos y precios
    3. **Controlar clientes:** Mantén actualizada tu base de datos de clientes
    4. **Ver historial:** Revisa todas las cotizaciones en la sección "Ver Proformas"
    
    👉 **Para empezar,** selecciona "Nueva Proforma" en el menú lateral.
    """)


# ========================= VER PROFORMAS (MEJORADO CON CARGA LAZY REAL) =========================

elif menu_option == "📊 Ver Proformas":
    st.markdown('<p class="main-header">📊 Historial de Proformas</p>', unsafe_allow_html=True)
    
    # Inicializar session state para los resultados
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    # Formulario de búsqueda MEJORADO
    with st.form("search_proformas_form"):
        st.markdown("### 🔍 Buscar Proformas")
        st.info("💡 **Carga Inteligente:** Las proformas se cargan solo cuando realizas una búsqueda. "
                "Esto mejora el rendimiento de la aplicación.")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            customer_search = st.text_input(
                "Cliente",
                placeholder="Nombre o empresa..."
            )
        
        with col2:
            model_search = st.text_input(
                "Modelo/Marca", 
                placeholder="Buscar equipo..."
            )
        
        with col3:
            proforma_number_search = st.text_input(
                "Número Proforma",
                placeholder="Ej: PF-20251022 o solo 20251022",
                help="Busca por cualquier parte del número de proforma"
            )
        
        with col4:
            date_from = st.date_input(
                "Fecha desde",
                value=datetime.now() - timedelta(days=30)
            )
        
        with col5:
            date_to = st.date_input(
                "Fecha hasta",
                value=datetime.now()
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por asesor
            with SessionLocal() as db:
                advisors = crud.list_advisors(db, active_only=False)
            advisor_options = ["Todos"] + [f"[{a.id}] {a.name}" for a in advisors]
            advisor_filter = st.selectbox("Asesor", advisor_options)
        
        with col2:
            # Filtro por tipo
            template_filter = st.selectbox(
                "Tipo de equipo",
                ["Todos", "Tractores", "Implementos"]
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacer
            search_submitted = st.form_submit_button(
                "🔍 Buscar Proformas",
                width='stretch',
                type="primary"
            )
    
    # Procesar búsqueda SOLO cuando se envía el formulario
    if search_submitted:
        with st.spinner("🔍 Buscando proformas..."):
            # Preparar filtros
            advisor_id = None
            if advisor_filter != "Todos":
                advisor_id = int(advisor_filter.split("]")[0].replace("[", ""))
            
            template = None
            if template_filter == "Tractores":
                template = "tractor"
            elif template_filter == "Implementos":
                template = "implement"
            
            # Realizar búsqueda avanzada
            with SessionLocal() as db:
                proformas = crud.search_proformas(
                    db,
                    customer_search=customer_search.strip() if customer_search else None,
                    model_search=model_search.strip() if model_search else None,
                    proforma_number=proforma_number_search.strip() if proforma_number_search else None,
                    date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
                    date_to=datetime.combine(date_to, datetime.max.time()) if date_to else None,
                    advisor_id=advisor_id,
                    template=template
                )
                
                # Construir datos para mostrar
                proformas_data = []
                for p in proformas:
                    customer_name = p.customer.name if p.customer else "N/A"
                    advisor_name = p.advisor.name if p.advisor else "Sin asesor"
                    items_count = len(p.items)
                    
                    proformas_data.append({
                        "id": p.id,
                        "number": p.number,
                        "date": p.date,
                        "customer_name": customer_name,
                        "advisor_name": advisor_name,
                        "template": p.template,
                        "currency": p.currency,
                        "total": p.total,
                        "items_count": items_count,
                        "pdf_path": p.pdf_path
                    })
        
        st.session_state.search_results = proformas_data
        st.session_state.search_performed = True
    
    # Mostrar resultados de búsqueda SOLO si se ha realizado una búsqueda
    if st.session_state.search_performed:
        proformas_data = st.session_state.search_results
        
        if proformas_data:
            st.markdown(f"### 📋 Resultados: {len(proformas_data)} proformas encontradas")
            
            # Crear tabla de visualización
            display_data = []
            for p in proformas_data:
                display_data.append({
                    "📌 Número": p["number"],
                    "📅 Fecha": p["date"].strftime("%d/%m/%Y"),
                    "👤 Cliente": p["customer_name"],
                    "👔 Asesor": p["advisor_name"],
                    "🚜 Tipo": "Tractores" if p["template"] == "tractor" else "Implementos",
                    "💰 Total": format_currency(p["total"], p["currency"]) if p["currency"] != "MIXED" else "Mixto",
                    "📦 Items": p["items_count"],
                    "ID": p["id"]
                })
            
            # Mostrar dataframe con selección
            df_display = st.dataframe(
                display_data,
                width='stretch',
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun"
            )
            
            # ACCIONES PARA PROFORMA SELECCIONADA
            if df_display.selection.rows:
                selected_idx = df_display.selection.rows[0]
                selected_proforma = proformas_data[selected_idx]
                
                st.markdown("---")
                st.markdown(f"### ✅ Proforma seleccionada: {selected_proforma['number']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # DESCARGAR PDF
                    if selected_proforma['pdf_path'] and Path(selected_proforma['pdf_path']).exists():
                        with open(selected_proforma['pdf_path'], "rb") as pdf_file:
                            st.download_button(
                                label="📥 Descargar PDF",
                                data=pdf_file.read(),
                                file_name=f"Proforma_{selected_proforma['number']}.pdf",
                                mime="application/pdf",
                                width='stretch'
                            )
                    else:
                        st.warning("📄 PDF no disponible")
                
                with col2:
                    # DUPLICAR PROFORMA - FUERA DEL FORM
                    if st.button("📋 Duplicar Proforma", width='stretch'):
                        st.session_state.show_duplicate_dialog = True
                        st.session_state.duplicate_proforma_id = selected_proforma['id']
                        st.session_state.duplicate_original_number = selected_proforma['number']
                        st.rerun()
                
                with col3:
                    # ELIMINAR PROFORMA - FUERA DEL FORM
                    if st.button("🗑️ Eliminar Proforma", width='stretch', type="secondary"):
                        st.session_state.show_delete_dialog = True
                        st.session_state.delete_proforma_id = selected_proforma['id']
                        st.session_state.delete_proforma_number = selected_proforma['number']
                        st.rerun()
        else:
            st.info("🔍 No se encontraron proformas con los criterios de búsqueda especificados.")
            
            # Información de debug para el usuario
            search_info = []
            if customer_search:
                search_info.append(f"Cliente: '{customer_search}'")
            if model_search:
                search_info.append(f"Modelo/Marca: '{model_search}'")
            if proforma_number_search:
                search_info.append(f"Número: '{proforma_number_search}'")
            if advisor_filter != "Todos":
                search_info.append(f"Asesor: {advisor_filter}")
            if template_filter != "Todos":
                search_info.append(f"Tipo: {template_filter}")
            
            if search_info:
                st.caption(f"**Criterios usados:** {' | '.join(search_info)}")
            
            st.markdown("""
            **Sugerencias:**
            - Verifica que las fechas sean correctas
            - Intenta con términos de búsqueda más amplios
            - Revisa los filtros de asesor y tipo de equipo
            - Para número de proforma, usa solo parte del número (ej: "20251022")
            """)
    else:
        # Mensaje inicial (sin carga automática) - ESTO ES LO IMPORTANTE
        st.markdown("### 🎯 Búsqueda Inteligente")
        st.info("""
        **¡Nueva funcionalidad!** Para mejorar el rendimiento, las proformas se cargan 
        únicamente cuando realizas una búsqueda específica.
        
        **Busca por:**
        - 👤 **Cliente:** Nombre o empresa
        - 🚜 **Modelo/Marca:** Cualquier equipo
        - 📌 **Número de Proforma:** Búsqueda exacta por número
        - 📅 **Fechas:** Rango personalizable
        - 👔 **Asesor:** Filtro por vendedor
        - 📋 **Tipo:** Tractores o implementos
        
        👆 **Utiliza el formulario de búsqueda de arriba para comenzar**
        """)

    # MODAL DE DUPLICACIÓN MEJORADO - FUERA DE CUALQUIER FORM
    if st.session_state.get("show_duplicate_dialog", False):
        st.markdown("---")
        
        with st.container():
            # Ventana modal estilizada
            st.markdown("""
            <div class="modal-dialog">
                <h3 style="color: #2E7D32; margin-bottom: 15px;">📋 Duplicar Proforma</h3>
                <p>Se creará una copia exacta con un nuevo número y fecha.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("duplicate_proforma_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_number = st.text_input(
                        "Nuevo número de proforma *",
                        value=generate_proforma_number(),
                        help="Número único para la nueva proforma"
                    )
                
                with col2:
                    new_date = st.date_input(
                        "Nueva fecha",
                        value=datetime.now(),
                        help="Fecha de la proforma duplicada"
                    )
                
                st.markdown("💡 **Nota:** La nueva proforma mantendrá todos los productos, precios, descuentos y configuración de la original.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("✅ Confirmar Duplicación", width='stretch', type="primary"):
                        if new_number:
                            try:
                                with SessionLocal() as db:
                                    # Verificar que el número no exista
                                    existing = crud.get_proforma_by_number(db, new_number)
                                    if existing:
                                        st.error(f"❌ Ya existe una proforma con el número {new_number}")
                                    else:
                                        # Duplicar proforma
                                        new_proforma = crud.duplicate_proforma(
                                            db,
                                            st.session_state.duplicate_proforma_id,
                                            new_number,
                                            datetime.combine(new_date, datetime.min.time())
                                        )
                                        
                                        if new_proforma:
                                            # Mostrar modal de éxito
                                            show_duplicate_modal(
                                                st.session_state.duplicate_original_number,
                                                new_number
                                            )
                                            
                                            # Limpiar estado del diálogo
                                            st.session_state.show_duplicate_dialog = False
                                            
                                            # Guardar datos para redirección a Nueva Proforma
                                            st.session_state.duplicate_data = {
                                                'number': new_number,
                                                'customer_id': new_proforma.customer_id,
                                                'template': new_proforma.template,
                                                'items': [
                                                    {
                                                        'brand_name': item.brand_name,
                                                        'model_name': item.model_name,
                                                        'year': item.year,
                                                        'description': item.description,
                                                        'qty': item.qty,
                                                        'unit_price': item.unit_price,
                                                        'discount_percent': item.discount_percent,
                                                        'currency': item.currency,
                                                        'tax_rate': item.tax_rate
                                                    }
                                                    for item in new_proforma.items
                                                ]
                                            }
                                            
                                            st.success(f"✅ Proforma {new_number} creada exitosamente")
                                            
                                            # ACTIVAR REDIRECCIÓN AUTOMÁTICA
                                            st.session_state.redirect_to_new_proforma = True
                                            
                                            # Información para el usuario
                                            st.info("🔄 **Redirigiendo automáticamente a 'Nueva Proforma'...**")
                                            
                                            # Forzar recarga para aplicar redirección
                                            st.rerun()
                                        else:
                                            st.error("❌ Error al duplicar la proforma")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                        else:
                            st.error("⚠️ El número de proforma es obligatorio")
                
                with col2:
                    if st.form_submit_button("❌ Cancelar", width='stretch'):
                        st.session_state.show_duplicate_dialog = False
                        st.rerun()

    # MODAL DE ELIMINACIÓN - FUERA DE CUALQUIER FORM
    if st.session_state.get("show_delete_dialog", False):
        st.markdown("---")
        
        with st.container():
            st.markdown("""
            <div class="modal-dialog">
                <h3 style="color: #F44336; margin-bottom: 15px;">🗑️ Eliminar Proforma</h3>
                <p style="color: #F44336;"><strong>¡ATENCIÓN!</strong> Esta acción es irreversible.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.warning(f"⚠️ **Vas a eliminar la proforma:** {st.session_state.delete_proforma_number}")
            st.info("📝 **Nota:** Solo se eliminará el registro de la base de datos. El archivo PDF (si existe) no se verá afectado.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Confirmar Eliminación", width='stretch', type="primary"):
                    try:
                        with SessionLocal() as db:
                            success = crud.delete_proforma(db, st.session_state.delete_proforma_id)
                            if success:
                                st.success("✅ Proforma eliminada correctamente")
                                # Limpiar resultado de búsqueda para forzar nueva búsqueda
                                st.session_state.search_performed = False
                                st.session_state.search_results = []
                                st.session_state.show_delete_dialog = False
                                st.rerun()
                            else:
                                st.error("❌ No se pudo eliminar la proforma")
                    except Exception as e:
                        st.error(f"❌ Error al eliminar: {e}")
            
            with col2:
                if st.button("❌ Cancelar", width='stretch'):
                    st.session_state.show_delete_dialog = False
                    st.rerun()


# ========================= NUEVA PROFORMA (CON MEJORAS EN MÉTRICAS) =========================

elif menu_option == "📄 Nueva Proforma":
    st.markdown('<p class="main-header">📄 Nueva Proforma</p>', unsafe_allow_html=True)
    
    # Verificar si hay datos de duplicación
    duplicate_data = st.session_state.get('duplicate_data', None)
    
    # Verificar datos necesarios
    with SessionLocal() as db:
        customers = crud.list_customers(db, active_only=True)
        advisors = crud.list_advisors(db, active_only=True)
    
    if not customers:
        st.error("❌ No hay clientes registrados.")
        st.info("💡 Ve a Mantenimientos → Clientes para crear uno.")
        st.stop()
    
    # Inicializar session_state para el PDF generado
    if 'pdf_generated' not in st.session_state:
        st.session_state.pdf_generated = False
        st.session_state.pdf_path = None
        st.session_state.pdf_info = {}
    
    # FORMULARIO PRINCIPAL
    with st.form("new_proforma_form", clear_on_submit=False):
        # Header de la proforma
        st.markdown("### 📋 Información General")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            template_option = st.selectbox(
                "Tipo de cotización *",
                ["🚜 Tractores", "🔧 Implementos"],
                index=0 if not duplicate_data or duplicate_data['template'] == 'tractor' else 1
            )
            template = "tractor" if template_option == "🚜 Tractores" else "implement"
        
        with col2:
            proforma_number = st.text_input(
                "N° de Proforma *",
                value=duplicate_data['number'] if duplicate_data else generate_proforma_number()
            )
        
        with col3:
            proforma_date = st.date_input(
                "Fecha *",
                value=datetime.now()
            )
        
        # Cliente
        st.markdown("### 👤 Cliente")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            customer_options = {f"[{c.id}] {c.name} - {c.company or 'Sin empresa'}": c for c in customers}
            selected_customer_label = st.selectbox(
                "Seleccionar cliente *",
                list(customer_options.keys()),
                index=0 if not duplicate_data else next(
                    (i for i, key in enumerate(customer_options.keys()) 
                     if customer_options[key].id == duplicate_data.get('customer_id')), 0
                )
            )
            selected_customer = customer_options[selected_customer_label]
        
        with col2:
            customer_attention = st.text_input(
                "A la atención de",
                value="",
                max_chars=MAX_CHARS.get("customer_attention", 80)
            )
        
        # Mostrar datos del cliente
        with st.expander("📋 Datos del cliente seleccionado", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"Nombre: {selected_customer.name}")
                st.text(f"Empresa: {selected_customer.company or 'N/A'}")
                st.text(f"Email: {selected_customer.email or 'N/A'}")
            with col2:
                st.text(f"Teléfono: {selected_customer.phone or 'N/A'}")
                st.text(f"Dirección: {selected_customer.address or 'N/A'}")
        
        # Asesor
        st.markdown("### 👔 Asesor")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if advisors:
                advisor_options = {f"[{a.id}] {a.name}": a for a in advisors}
                advisor_options["Sin asesor"] = None
                selected_advisor_label = st.selectbox(
                    "Seleccionar asesor",
                    list(advisor_options.keys())
                )
                selected_advisor = advisor_options[selected_advisor_label]
            else:
                st.info("No hay asesores registrados. Se generará sin asesor.")
                selected_advisor = None
        
        with col2:
            validity_days = st.number_input(
                "Vigencia (días)",
                min_value=1,
                max_value=365,
                value=15,
                step=1
            )
        
        # Selección de modelos
        st.markdown("### 📦 Productos")
        
        # Obtener y filtrar modelos dentro de una sesión
        with SessionLocal() as db:
            all_models = crud.list_models(db, active_only=True, equipment_type=template)
            
            # Construir lista de modelos mientras la sesión está activa
            models_list = [
                {
                    "id": m.id,
                    "label": f"[{m.id}] {m.brand.name} - {m.name}",
                    "brand_name": m.brand.name,
                    "model_name": m.name,
                    "base_price": m.base_price,
                    "description": m.description,
                    "image_path": m.image_path,
                    "brand_id": m.brand_id
                }
                for m in all_models
            ]
        
        if not models_list:
            st.error(f"❌ No hay modelos de tipo {template_option} registrados.")
            st.info("💡 Ve a Mantenimientos → Modelos para crear uno.")
            st.form_submit_button("Generar Proforma", disabled=True)
            st.stop()
        
        # Pre-cargar modelos si es duplicación
        selected_models_labels = []
        if duplicate_data and duplicate_data.get('items'):
            for item in duplicate_data['items']:
                label = f"{item['brand_name']} {item['model_name']}"
                # Buscar el label exacto en models_list
                matching_label = next(
                    (m["label"] for m in models_list 
                     if item['brand_name'] in m["label"] and item['model_name'] in m["label"]), 
                    None
                )
                if matching_label and matching_label not in selected_models_labels:
                    selected_models_labels.append(matching_label)
        
        # Selector de modelos
        selected_models_labels = st.multiselect(
            "Selecciona uno o más modelos",
            [m["label"] for m in models_list],
            default=selected_models_labels,
            help="Cada modelo seleccionado ocupará una página en el PDF"
        )
        
        if not selected_models_labels:
            st.warning("⚠️ Selecciona al menos un modelo para continuar.")
        
        # Configuración de items
        items_data = []
        
        if selected_models_labels:
            st.markdown("#### Configuración de Productos")
            
            for model_label in selected_models_labels:
                model_info = next(m for m in models_list if m["label"] == model_label)
                
                # Buscar datos previos si es duplicación
                prev_item = None
                if duplicate_data and duplicate_data.get('items'):
                    prev_item = next(
                        (item for item in duplicate_data['items'] 
                         if item['brand_name'] == model_info['brand_name'] and 
                            item['model_name'] == model_info['model_name']), 
                        None
                    )
                
                with st.expander(f"🔧 {model_info['brand_name']} - {model_info['model_name']}", expanded=True):
                    cols = st.columns([1, 1, 1, 1.2, 0.8, 0.8, 2])
                    
                    with cols[0]:
                        qty = st.number_input(
                            "Cantidad",
                            min_value=1,
                            value=prev_item['qty'] if prev_item else 1,
                            step=1,
                            key=f"qty_{model_info['id']}"
                        )
                    
                    with cols[1]:
                        year = None
                        if template == "tractor":
                            year = st.number_input(
                                "Año",
                                min_value=1900,
                                max_value=2100,
                                value=prev_item['year'] if prev_item and prev_item['year'] else datetime.now().year,
                                step=1,
                                key=f"year_{model_info['id']}"
                            )
                    
                    with cols[2]:
                        currency = st.selectbox(
                            "Moneda",
                            ["CRC", "USD"],
                            index=0 if not prev_item or prev_item['currency'] == 'CRC' else 1,
                            key=f"currency_{model_info['id']}"
                        )
                    
                    with cols[3]:
                        unit_price = st.number_input(
                            "Precio Unit.",
                            min_value=0.0,
                            value=float(prev_item['unit_price']) if prev_item else float(model_info['base_price']),
                            step=100.0,
                            format="%.2f",
                            key=f"price_{model_info['id']}"
                        )
                    
                    with cols[4]:
                        discount_percent = st.number_input(
                            "Desc %",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(prev_item['discount_percent']) if prev_item else 0.0,
                            step=0.5,
                            format="%.2f",
                            key=f"discount_{model_info['id']}"
                        )
                    
                    with cols[5]:
                        # IVA EDITABLE
                        tax_rate = st.number_input(
                            "IVA %",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(prev_item['tax_rate']) if prev_item else 13.0,
                            step=0.5,
                            format="%.2f",
                            key=f"tax_{model_info['id']}",
                            help="Ajustable para exoneraciones"
                        )
                    
                    # Calcular totales con IVA personalizado
                    line_subtotal = qty * unit_price
                    discount_amount = line_subtotal * (discount_percent / 100)
                    line_subtotal_after_discount = line_subtotal - discount_amount
                    line_tax = round(line_subtotal_after_discount * (tax_rate / 100), 2)
                    line_total = line_subtotal_after_discount + line_tax
                    
                    # Mostrar totales CON TAMAÑO DE FUENTE REDUCIDO
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    col_totals = st.columns(5)
                    col_totals[0].metric("Subtotal", format_currency(line_subtotal, currency))
                    if discount_percent > 0:
                        col_totals[1].metric("Descuento", format_currency(discount_amount, currency))
                    col_totals[2].metric("Subtotal Neto", format_currency(line_subtotal_after_discount, currency))
                    col_totals[3].metric(f"IVA {tax_rate}%", format_currency(line_tax, currency))
                    col_totals[4].metric("Total Línea", format_currency(line_total, currency))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    items_data.append({
                        "model_id": model_info['id'],
                        "brand_name": model_info['brand_name'],
                        "model_name": model_info['model_name'],
                        "year": year,
                        "description": prev_item['description'] if prev_item else model_info['description'],
                        "image_path": model_info['image_path'],
                        "qty": qty,
                        "unit_price": unit_price,
                        "discount_percent": discount_percent,
                        "discount_amount": discount_amount,
                        "line_subtotal": line_subtotal,
                        "line_total": line_total,
                        "currency": currency,
                        "tax_rate": tax_rate  # IVA personalizado
                    })
            
            # Totales generales CON TAMAÑO REDUCIDO
            st.markdown("---")
            st.markdown("### 💰 Totales")
            
            currencies_in_quote = {item["currency"] for item in items_data}
            
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            
            if len(currencies_in_quote) == 1:
                # Una sola moneda
                cur = currencies_in_quote.pop()
                
                # Agrupar items por tasa de IVA
                tax_rates = {item["tax_rate"] for item in items_data}
                
                subtotal = sum(item["line_subtotal"] for item in items_data)
                discount_total = sum(item["discount_amount"] for item in items_data)
                subtotal_after_discount = subtotal - discount_total
                
                # Calcular IVA ponderado si hay múltiples tasas
                if len(tax_rates) == 1:
                    single_tax_rate = tax_rates.pop()
                    tax = round(subtotal_after_discount * (single_tax_rate / 100), 2)
                    tax_label = f"IVA {single_tax_rate}%"
                else:
                    # IVA mixto: calcular por cada item
                    tax = sum(
                        round((item["qty"] * item["unit_price"] - item["discount_amount"]) * (item["tax_rate"] / 100), 2)
                        for item in items_data
                    )
                    tax_label = "IVA (mixto)"
                
                total = subtotal_after_discount + tax
                
                cols = st.columns(5)
                cols[0].metric("Subtotal", format_currency(subtotal, cur))
                if discount_total > 0:
                    cols[1].metric("Descuento", format_currency(discount_total, cur))
                cols[2].metric("Subtotal Neto", format_currency(subtotal_after_discount, cur))
                cols[3].metric(tax_label, format_currency(tax, cur))
                cols[4].metric("**TOTAL**", format_currency(total, cur))
                
                totals = {
                    "subtotal": subtotal,
                    "discount": discount_total,
                    "subtotal_after_discount": subtotal_after_discount,
                    "tax": tax,
                    "total": total,
                    "currency": cur,
                    "tax_rate": single_tax_rate if len(tax_rates) == 1 else "mixto"
                }
            else:
                # Múltiples monedas
                totals = {}
                st.warning("⚠️ Productos en diferentes monedas. Los totales se mostrarán por separado.")
                
                for cur in sorted(currencies_in_quote):
                    st.markdown(f"#### {cur}")
                    
                    cur_items = [item for item in items_data if item["currency"] == cur]
                    subtotal = sum(item["line_subtotal"] for item in cur_items)
                    discount_total = sum(item["discount_amount"] for item in cur_items)
                    subtotal_after_discount = subtotal - discount_total
                    
                    # IVA por moneda
                    tax_rates_cur = {item["tax_rate"] for item in cur_items}
                    
                    if len(tax_rates_cur) == 1:
                        single_tax_rate = tax_rates_cur.pop()
                        tax = round(subtotal_after_discount * (single_tax_rate / 100), 2)
                        tax_label = f"IVA {single_tax_rate}%"
                    else:
                        tax = sum(
                            round((item["qty"] * item["unit_price"] - item["discount_amount"]) * (item["tax_rate"] / 100), 2)
                            for item in cur_items
                        )
                        tax_label = "IVA (mixto)"
                    
                    total = subtotal_after_discount + tax
                    
                    cols = st.columns(5)
                    cols[0].metric("Subtotal", format_currency(subtotal, cur))
                    if discount_total > 0:
                        cols[1].metric("Descuento", format_currency(discount_total, cur))
                    cols[2].metric("Sub. Neto", format_currency(subtotal_after_discount, cur))
                    cols[3].metric(tax_label, format_currency(tax, cur))
                    cols[4].metric("Total", format_currency(total, cur))
                    
                    totals[cur] = {
                        "subtotal": subtotal,
                        "discount": discount_total,
                        "subtotal_after_discount": subtotal_after_discount,
                        "tax": tax,
                        "total": total,
                        "currency": cur,
                        "tax_rate": single_tax_rate if len(tax_rates_cur) == 1 else "mixto"
                    }
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Personalización (opcional)
        st.markdown("---")
        st.markdown("### 📝 Personalización (Opcional)")
        
        with st.expander("Personalizar términos y condiciones"):
            with SessionLocal() as db:
                default_terms = crud.get_config(db, f"terms_{template}", "")
            
            custom_terms = st.text_area(
                "Términos personalizados",
                value="",
                height=150,
                placeholder="Deja vacío para usar los términos por defecto",
                max_chars=MAX_CHARS.get(f"terms_{template}", 800)
            )
            
            st.info(f"💡 Términos por defecto: {len(default_terms)} caracteres")
        
        with st.expander("Personalizar nota fiscal"):
            with SessionLocal() as db:
                default_fiscal = crud.get_config(db, "fiscal_note", "")
            
            custom_fiscal = st.text_area(
                "Nota fiscal personalizada",
                value="",
                height=100,
                placeholder="Deja vacío para usar la nota por defecto",
                max_chars=MAX_CHARS.get("fiscal_note", 400)
            )
            
            st.info(f"💡 Nota por defecto: {len(default_fiscal)} caracteres")
        
        # Botón de generación
        st.markdown("---")
        submitted = st.form_submit_button(
            "📄 Generar Proforma en PDF",
            width="stretch",
            type="primary"
        )
        
        if submitted:
            # Validaciones
            errors = []
            
            if not proforma_number:
                errors.append("El número de proforma es obligatorio")
            if not selected_models_labels:
                errors.append("Debes seleccionar al menos un modelo")
            
            # Verificar duplicidad de número
            with SessionLocal() as db:
                existing = crud.get_proforma_by_number(db, proforma_number)
                if existing:
                    errors.append(f"Ya existe una proforma con el número {proforma_number}")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                try:
                    # Obtener configuración
                    with SessionLocal() as db:
                        config = crud.get_all_config(db)
                    
                    # Preparar datos del header con logos configurables
                    header_data = {
                        "title": "COTIZACIÓN",
                        "company_name": config.get("company_name", ""),
                        "company_address": config.get("company_address", ""),
                        "company_phone": config.get("company_phone", ""),
                        "company_email": config.get("company_email", ""),
                        "company_web": config.get("company_web", ""),
                        "date": proforma_date.strftime("%Y-%m-%d"),
                        "number": proforma_number,
                        "customer_name": selected_customer.name,
                        "customer_company": selected_customer.company or "",
                        "customer_attention": customer_attention,
                        "customer_email": selected_customer.email or "",
                        "customer_phone": selected_customer.phone or "",
                        "customer_address": selected_customer.address or "",
                        "validity_days": validity_days,
                        "advisor_name": selected_advisor.name if selected_advisor else "",
                        "advisor_phone": selected_advisor.phone if selected_advisor else "",
                        "advisor_email": selected_advisor.email if selected_advisor else "",
                        "terms": custom_terms.strip() or config.get(f"terms_{template}", ""),
                        "fiscal_note": custom_fiscal.strip() or config.get("fiscal_note", ""),
                        # Logos configurables
                        "logo_left_path": config.get("logo_left_path", str(LOGOS_DIR / "colono.png")),
                        "logo_right_path": config.get("logo_right_path", str(LOGOS_DIR / "massey.png"))
                    }
                    
                    # Generar PDF
                    output_path = OUTPUTS_DIR / f"Proforma_{proforma_number}.pdf"
                    build_proforma_pdf(
                        output_path,
                        header_data,
                        items_data,
                        totals,
                        template=template
                    )
                    
                    # Guardar en base de datos
                    with SessionLocal() as db:
                        proforma = crud.create_proforma(
                            db,
                            number=proforma_number,
                            customer_id=selected_customer.id,
                            template=template,
                            items_data=items_data,
                            advisor_id=selected_advisor.id if selected_advisor else None,
                            customer_attention=customer_attention,
                            validity_days=validity_days,
                            date=datetime.combine(proforma_date, datetime.min.time()),
                            custom_terms=custom_terms.strip(),
                            custom_fiscal_note=custom_fiscal.strip()
                        )
                        
                        # Actualizar ruta del PDF
                        proforma.pdf_path = str(output_path)
                        db.commit()
                    
                    # Limpiar datos de duplicación si existen
                    if 'duplicate_data' in st.session_state:
                        del st.session_state.duplicate_data
                    
                    # Guardar información en session_state
                    st.session_state.pdf_generated = True
                    st.session_state.pdf_path = output_path
                    st.session_state.pdf_info = {
                        "number": proforma_number,
                        "customer": selected_customer.name,
                        "template": template_option,
                        "date": proforma_date.strftime('%d/%m/%Y'),
                        "products": len(items_data),
                        "pages": len(items_data)
                    }
                    
                    st.success("✅ ¡Proforma generada exitosamente!")
                    st.balloons()
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error al generar la proforma: {e}")
                    st.exception(e)
    
    # FUERA DEL FORMULARIO: Mostrar botón de descarga si hay PDF generado
    if st.session_state.get('pdf_generated', False) and st.session_state.get('pdf_path'):
        st.markdown("---")
        st.markdown("### ✅ Proforma Generada")
        
        # Mostrar resumen
        with st.expander("📋 Resumen de la proforma", expanded=True):
            info = st.session_state.pdf_info
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**N° Proforma:** {info['number']}")
                st.markdown(f"**Cliente:** {info['customer']}")
                st.markdown(f"**Tipo:** {info['template']}")
            with col2:
                st.markdown(f"**Fecha:** {info['date']}")
                st.markdown(f"**Productos:** {info['products']}")
                st.markdown(f"**Páginas PDF:** {info['pages']}")
        
        # Botón de descarga (FUERA del form)
        with open(st.session_state.pdf_path, "rb") as pdf_file:
            st.download_button(
                label="📥 Descargar PDF",
                data=pdf_file.read(),
                file_name=st.session_state.pdf_path.name,
                mime="application/pdf",
                width="stretch",
                type="primary"
            )
        
        # Botón para crear otra proforma
        if st.button("🆕 Crear Nueva Proforma", width="stretch"):
            st.session_state.pdf_generated = False
            st.session_state.pdf_path = None
            st.session_state.pdf_info = {}
            st.rerun()


# ========================= MANTENIMIENTO: CLIENTES =========================

elif menu_option == "📋 Mantenimientos" and submenu == "👥 Clientes":
    st.markdown('<p class="main-header">👥 Gestión de Clientes</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Lista de Clientes", "➕ Crear/Editar"])
    
    with tab1:
        st.markdown("### Lista de Clientes")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Buscar", placeholder="Buscar por nombre, empresa o email...")
        with col2:
            show_inactive = st.checkbox("Mostrar inactivos", value=False)
        
        with SessionLocal() as db:
            customers = crud.list_customers(db, active_only=not show_inactive, search=search or None)
        
        if customers:
            st.dataframe(
                [
                    {
                        "ID": c.id,
                        "Nombre": c.name,
                        "Empresa": c.company or "-",
                        "Email": c.email or "-",
                        "Teléfono": c.phone or "-",
                        "Estado": "✅ Activo" if c.active else "❌ Inactivo"
                    }
                    for c in customers
                ],
                width="stretch",
                hide_index=True
            )
            st.caption(f"📊 Total: {len(customers)} clientes")
        else:
            st.info("No se encontraron clientes.")
    
    with tab2:
        st.markdown("### Crear/Editar Cliente")
        
        operation = st.radio("Operación", ["➕ Crear Nuevo", "✏️ Editar Existente"], horizontal=True)
        
        with st.form("customer_form"):
            customer_to_edit = None
            
            if operation == "✏️ Editar Existente":
                with SessionLocal() as db:
                    all_customers = crud.list_customers(db, active_only=False)
                
                if not all_customers:
                    st.warning("No hay clientes para editar.")
                    st.form_submit_button("Guardar", disabled=True)
                    st.stop()
                
                customer_options = {f"[{c.id}] {c.name}": c for c in all_customers}
                selected = st.selectbox("Seleccionar cliente", list(customer_options.keys()))
                customer_to_edit = customer_options[selected]
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Nombre *",
                    value=customer_to_edit.name if customer_to_edit else "",
                    max_chars=MAX_CHARS.get("customer_name", 80)
                )
                if name:
                    show_char_counter("customer_name", len(name))
                
                company = st.text_input(
                    "Empresa",
                    value=customer_to_edit.company if customer_to_edit else "",
                    max_chars=MAX_CHARS.get("customer_company", 80)
                )
                if company:
                    show_char_counter("customer_company", len(company))
                
                email = st.text_input(
                    "Email",
                    value=customer_to_edit.email if customer_to_edit else ""
                )
            
            with col2:
                phone = st.text_input(
                    "Teléfono",
                    value=customer_to_edit.phone if customer_to_edit else ""
                )
                
                active = st.checkbox(
                    "Cliente activo",
                    value=customer_to_edit.active if customer_to_edit else True
                )
            
            address = st.text_area(
                "Dirección",
                value=customer_to_edit.address if customer_to_edit else "",
                height=100
            )
            
            submitted = st.form_submit_button("💾 Guardar", width="stretch")
            
            if submitted:
                if not name:
                    st.error("⚠️ El nombre es obligatorio")
                elif email and not validate_email(email):
                    st.error("⚠️ Email no válido")
                else:
                    try:
                        with SessionLocal() as db:
                            if operation == "➕ Crear Nuevo":
                                crud.create_customer(
                                    db, name=name, company=company,
                                    email=email, phone=phone,
                                    address=address, active=active
                                )
                                st.success("✅ Cliente creado exitosamente!")
                            else:
                                crud.update_customer(
                                    db, customer_to_edit.id,
                                    name=name, company=company,
                                    email=email, phone=phone,
                                    address=address, active=active
                                )
                                st.success("✅ Cliente actualizado!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        # Eliminar cliente
        if operation == "✏️ Editar Existente":
            st.markdown("---")
            st.markdown("### 🗑️ Eliminar Cliente")
            st.warning("⚠️ Esta acción es permanente.")
            
            if st.button("🗑️ Eliminar Cliente Seleccionado", type="secondary"):
                try:
                    with SessionLocal() as db:
                        crud.delete_customer(db, customer_to_edit.id)
                    st.success(f"✅ Cliente eliminado")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ========================= MANTENIMIENTO: ASESORES =========================

elif menu_option == "📋 Mantenimientos" and submenu == "👔 Asesores":
    st.markdown('<p class="main-header">👔 Gestión de Asesores</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Lista de Asesores", "➕ Crear/Editar"])
    
    with tab1:
        st.markdown("### Lista de Asesores")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Buscar", placeholder="Buscar por nombre o email...")
        with col2:
            show_inactive = st.checkbox("Mostrar inactivos", value=False)
        
        with SessionLocal() as db:
            advisors = crud.list_advisors(db, active_only=not show_inactive, search=search or None)
        
        if advisors:
            st.dataframe(
                [
                    {
                        "ID": a.id,
                        "Nombre": a.name,
                        "Email": a.email or "-",
                        "Teléfono": a.phone or "-",
                        "Estado": "✅ Activo" if a.active else "❌ Inactivo"
                    }
                    for a in advisors
                ],
                width="stretch",
                hide_index=True
            )
            st.caption(f"📊 Total: {len(advisors)} asesores")
        else:
            st.info("No se encontraron asesores.")
    
    with tab2:
        st.markdown("### Crear/Editar Asesor")
        
        operation = st.radio("Operación", ["➕ Crear Nuevo", "✏️ Editar Existente"], horizontal=True)
        
        with st.form("advisor_form"):
            advisor_to_edit = None
            
            if operation == "✏️ Editar Existente":
                with SessionLocal() as db:
                    all_advisors = crud.list_advisors(db, active_only=False)
                
                if not all_advisors:
                    st.warning("No hay asesores para editar.")
                    st.form_submit_button("Guardar", disabled=True)
                    st.stop()
                
                advisor_options = {f"[{a.id}] {a.name}": a for a in all_advisors}
                selected = st.selectbox("Seleccionar asesor", list(advisor_options.keys()))
                advisor_to_edit = advisor_options[selected]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input(
                    "Nombre *",
                    value=advisor_to_edit.name if advisor_to_edit else "",
                    max_chars=MAX_CHARS.get("advisor_name", 60)
                )
                if name:
                    show_char_counter("advisor_name", len(name))
            
            with col2:
                email = st.text_input(
                    "Email",
                    value=advisor_to_edit.email if advisor_to_edit else "",
                    max_chars=MAX_CHARS.get("advisor_email", 50)
                )
                if email:
                    show_char_counter("advisor_email", len(email))
            
            with col3:
                phone = st.text_input(
                    "Teléfono",
                    value=advisor_to_edit.phone if advisor_to_edit else "",
                    max_chars=MAX_CHARS.get("advisor_phone", 30)
                )
                if phone:
                    show_char_counter("advisor_phone", len(phone))
            
            active = st.checkbox(
                "Asesor activo",
                value=advisor_to_edit.active if advisor_to_edit else True
            )
            
            submitted = st.form_submit_button("💾 Guardar", width="stretch")
            
            if submitted:
                if not name:
                    st.error("⚠️ El nombre es obligatorio")
                elif email and not validate_email(email):
                    st.error("⚠️ Email no válido")
                else:
                    try:
                        with SessionLocal() as db:
                            if operation == "➕ Crear Nuevo":
                                crud.create_advisor(
                                    db, name=name, email=email,
                                    phone=phone, active=active
                                )
                                st.success("✅ Asesor creado!")
                            else:
                                crud.update_advisor(
                                    db, advisor_to_edit.id,
                                    name=name, email=email,
                                    phone=phone, active=active
                                )
                                st.success("✅ Asesor actualizado!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        # Eliminar asesor
        if operation == "✏️ Editar Existente":
            st.markdown("---")
            st.markdown("### 🗑️ Eliminar Asesor")
            st.warning("⚠️ Esta acción es permanente.")
            
            if st.button("🗑️ Eliminar Asesor Seleccionado", type="secondary"):
                try:
                    with SessionLocal() as db:
                        crud.delete_advisor(db, advisor_to_edit.id)
                    st.success(f"✅ Asesor eliminado")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ========================= MANTENIMIENTO: MARCAS =========================

elif menu_option == "📋 Mantenimientos" and submenu == "🏭 Marcas":
    st.markdown('<p class="main-header">🏭 Gestión de Marcas</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Lista de Marcas", "➕ Crear/Editar"])
    
    with tab1:
        st.markdown("### Lista de Marcas")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            filter_type = st.selectbox(
                "Filtrar por tipo",
                ["Todos", "Tractores", "Implementos"]
            )
        with col2:
            show_inactive = st.checkbox("Mostrar inactivas", value=False)
        
        type_filter = None
        if filter_type == "Tractores":
            type_filter = "tractor"
        elif filter_type == "Implementos":
            type_filter = "implement"
        
        # Acceder a las relaciones DENTRO de la sesión
        with SessionLocal() as db:
            brands = crud.list_brands(db, equipment_type=type_filter, active_only=not show_inactive)
            
            # Construir datos mientras la sesión está activa
            brands_data = [
                {
                    "ID": b.id,
                    "Nombre": b.name,
                    "Tipo": "🚜 Tractor" if b.equipment_type == "tractor" else "🔧 Implemento",
                    "Modelos": len(b.models),
                    "Estado": "✅ Activa" if b.active else "❌ Inactiva"
                }
                for b in brands
            ]
        
        if brands_data:
            st.dataframe(brands_data, width="stretch", hide_index=True)
            st.caption(f"📊 Total: {len(brands_data)} marcas")
        else:
            st.info("No se encontraron marcas.")
    
    with tab2:
        st.markdown("### Crear/Editar Marca")
        
        operation = st.radio("Operación", ["➕ Crear Nueva", "✏️ Editar Existente"], horizontal=True)
        
        with st.form("brand_form"):
            brand_to_edit = None
            
            if operation == "✏️ Editar Existente":
                with SessionLocal() as db:
                    all_brands = crud.list_brands(db, active_only=False)
                
                if not all_brands:
                    st.warning("No hay marcas para editar.")
                    st.form_submit_button("Guardar", disabled=True)
                    st.stop()
                
                brand_options = {f"[{b.id}] {b.name} ({b.equipment_type})": b for b in all_brands}
                selected = st.selectbox("Seleccionar marca", list(brand_options.keys()))
                brand_to_edit = brand_options[selected]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input(
                    "Nombre de la marca *",
                    value=brand_to_edit.name if brand_to_edit else "",
                    placeholder="Ej: Massey Ferguson"
                )
            
            with col2:
                equipment_type = st.selectbox(
                    "Tipo de equipo *",
                    ["Tractor", "Implemento"],
                    index=0 if not brand_to_edit or brand_to_edit.equipment_type == "tractor" else 1
                )
                equipment_type_key = "tractor" if equipment_type == "Tractor" else "implement"
            
            with col3:
                active = st.checkbox(
                    "Marca activa",
                    value=brand_to_edit.active if brand_to_edit else True
                )
            
            submitted = st.form_submit_button("💾 Guardar", width="stretch")
            
            if submitted:
                if not name:
                    st.error("⚠️ El nombre es obligatorio")
                else:
                    try:
                        with SessionLocal() as db:
                            if operation == "➕ Crear Nueva":
                                crud.create_brand(
                                    db, name=name,
                                    equipment_type=equipment_type_key,
                                    active=active
                                )
                                st.success("✅ Marca creada!")
                            else:
                                crud.update_brand(
                                    db, brand_to_edit.id,
                                    name=name,
                                    equipment_type=equipment_type_key,
                                    active=active
                                )
                                st.success("✅ Marca actualizada!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        # Eliminar marca
        if operation == "✏️ Editar Existente":
            st.markdown("---")
            st.markdown("### 🗑️ Eliminar Marca")
            st.warning("⚠️ Esto eliminará también todos los modelos asociados.")
            
            if st.button("🗑️ Eliminar Marca Seleccionada", type="secondary"):
                try:
                    with SessionLocal() as db:
                        crud.delete_brand(db, brand_to_edit.id)
                    st.success(f"✅ Marca eliminada")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ========================= MANTENIMIENTO: MODELOS =========================

elif menu_option == "📋 Mantenimientos" and submenu == "📦 Modelos":
    st.markdown('<p class="main-header">📦 Gestión de Modelos</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Lista de Modelos", "➕ Crear/Editar"])
    
    with tab1:
        st.markdown("### Lista de Modelos")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            filter_type = st.selectbox(
                "Tipo de equipo",
                ["Todos", "Tractores", "Implementos"]
            )
        with col2:
            with SessionLocal() as db:
                all_brands = crud.list_brands(db, active_only=True)
            
            brand_filter_options = ["Todas"] + [b.name for b in all_brands]
            brand_filter = st.selectbox("Marca", brand_filter_options)
        with col3:
            show_inactive = st.checkbox("Inactivos", value=False)
        
        # Aplicar filtros
        type_filter = None
        if filter_type == "Tractores":
            type_filter = "tractor"
        elif filter_type == "Implementos":
            type_filter = "implement"
        
        brand_id_filter = None
        if brand_filter != "Todas":
            brand_obj = next((b for b in all_brands if b.name == brand_filter), None)
            if brand_obj:
                brand_id_filter = brand_obj.id
        
        # Acceder a las relaciones DENTRO de la sesión
        with SessionLocal() as db:
            models = crud.list_models(
                db,
                brand_id=brand_id_filter,
                equipment_type=type_filter,
                active_only=not show_inactive
            )
            
            # Construir datos mientras la sesión está activa
            models_data = [
                {
                    "ID": m.id,
                    "Marca": m.brand.name,
                    "Modelo": m.name,
                    "Tipo": "🚜 Tractor" if m.brand.equipment_type == "tractor" else "🔧 Implemento",
                    "Precio Base": format_currency(m.base_price),
                    "Estado": "✅ Activo" if m.active else "❌ Inactivo"
                }
                for m in models
            ]
        
        if models_data:
            st.dataframe(models_data, width="stretch", hide_index=True)
            st.caption(f"📊 Total: {len(models_data)} modelos")
        else:
            st.info("No se encontraron modelos.")
    
    with tab2:
        st.markdown("### Crear/Editar Modelo")
        
        operation = st.radio("Operación", ["➕ Crear Nuevo", "✏️ Editar Existente"], horizontal=True)
        
        with st.form("model_form"):
            model_to_edit = None
            
            if operation == "✏️ Editar Existente":
                with SessionLocal() as db:
                    all_models = crud.list_models(db, active_only=False)
                    
                    # Construir opciones dentro de la sesión
                    model_options_list = [
                        {
                            "label": f"[{m.id}] {m.brand.name} - {m.name}",
                            "model": m,
                            "brand_name": m.brand.name,
                            "brand_type": m.brand.equipment_type
                        }
                        for m in all_models
                    ]
                
                if not model_options_list:
                    st.warning("No hay modelos para editar.")
                    st.form_submit_button("Guardar", disabled=True)
                    st.stop()
                
                model_options = {item["label"]: item["model"] for item in model_options_list}
                selected = st.selectbox("Seleccionar modelo", list(model_options.keys()))
                model_to_edit = model_options[selected]
            
            # Obtener marcas activas
            with SessionLocal() as db:
                active_brands = crud.list_brands(db, active_only=True)
                brands_list = [
                    {
                        "label": f"{b.name} ({b.equipment_type})",
                        "brand": b,
                        "id": b.id,
                        "name": b.name,
                        "type": b.equipment_type
                    }
                    for b in active_brands
                ]
            
            if not brands_list:
                st.error("❌ No hay marcas activas. Crea una marca primero.")
                st.form_submit_button("Guardar", disabled=True)
                st.stop()
            
            col1, col2 = st.columns(2)
            
            with col1:
                brand_options_dict = {item["label"]: item for item in brands_list}
                
                if model_to_edit:
                    # Buscar la marca del modelo en la lista de marcas
                    current_brand_label = None
                    for label, brand_info in brand_options_dict.items():
                        if brand_info["id"] == model_to_edit.brand_id:
                            current_brand_label = label
                            break
                    
                    default_index = list(brand_options_dict.keys()).index(current_brand_label) if current_brand_label else 0
                else:
                    default_index = 0
                
                selected_brand_label = st.selectbox(
                    "Marca *",
                    list(brand_options_dict.keys()),
                    index=default_index
                )
                selected_brand = brand_options_dict[selected_brand_label]["brand"]
                
                name = st.text_input(
                    "Nombre del modelo *",
                    value=model_to_edit.name if model_to_edit else "",
                    placeholder="Ej: MF 4283"
                )
                
                base_price = st.number_input(
                    "Precio base (₡)",
                    min_value=0.0,
                    value=float(model_to_edit.base_price) if model_to_edit else 0.0,
                    step=1000.0,
                    format="%.2f"
                )
            
            with col2:
                image_file = st.file_uploader(
                    "Imagen del modelo",
                    type=["jpg", "jpeg", "png"],
                    help="Tamaño recomendado: 800x600px"
                )
                
                active = st.checkbox(
                    "Modelo activo",
                    value=model_to_edit.active if model_to_edit else True
                )
            
            description = st.text_area(
                "Especificaciones técnicas *",
                value=model_to_edit.description if model_to_edit else "",
                height=200,
                max_chars=MAX_CHARS.get("product_description", 1000),
                placeholder="Describe las características técnicas del modelo..."
            )
            if description:
                show_char_counter("product_description", len(description))
            
            submitted = st.form_submit_button("💾 Guardar", width="stretch")
            
            if submitted:
                if not name or not description:
                    st.error("⚠️ El nombre y las especificaciones son obligatorios")
                else:
                    try:
                        image_path = save_uploaded_image(image_file) if image_file else None
                        
                        with SessionLocal() as db:
                            if operation == "➕ Crear Nuevo":
                                crud.create_model(
                                    db,
                                    brand_id=selected_brand.id,
                                    name=name,
                                    description=description,
                                    base_price=base_price,
                                    image_path=image_path or "",
                                    active=active
                                )
                                st.success("✅ Modelo creado!")
                            else:
                                # Si no hay nueva imagen, mantener la existente
                                if not image_path:
                                    image_path = model_to_edit.image_path
                                
                                crud.update_model(
                                    db, model_to_edit.id,
                                    brand_id=selected_brand.id,
                                    name=name,
                                    description=description,
                                    base_price=base_price,
                                    image_path=image_path,
                                    active=active
                                )
                                st.success("✅ Modelo actualizado!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        # Eliminar modelo
        if operation == "✏️ Editar Existente":
            st.markdown("---")
            st.markdown("### 🗑️ Eliminar Modelo")
            st.warning("⚠️ Esta acción es permanente.")
            
            if st.button("🗑️ Eliminar Modelo Seleccionado", type="secondary"):
                try:
                    with SessionLocal() as db:
                        crud.delete_model(db, model_to_edit.id)
                    st.success(f"✅ Modelo eliminado")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ========================= CONFIGURACIÓN =========================

elif menu_option == "⚙️ Configuración":
    st.markdown('<p class="main-header">⚙️ Configuración del Sistema</p>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🏢 Datos de la Empresa", "🖼️ Logos", "🚜 Términos Tractores", "🔧 Términos Implementos", "📄 Nota Fiscal"])
    
    # Tab: Datos de la empresa
    with tabs[0]:
        st.markdown("### Datos de la Empresa")
        st.info("💡 Esta información aparecerá en todas las proformas.")
        
        with st.form("company_form"):
            with SessionLocal() as db:
                company_name = crud.get_config(db, "company_name", "Colono")
                company_address = crud.get_config(db, "company_address", "")
                company_phone = crud.get_config(db, "company_phone", "")
                company_email = crud.get_config(db, "company_email", "")
                company_web = crud.get_config(db, "company_web", "")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name_input = st.text_input(
                    "Nombre de la empresa",
                    value=company_name,
                    max_chars=MAX_CHARS.get("company_name", 60)
                )
                if name_input:
                    show_char_counter("company_name", len(name_input))
                
                address_input = st.text_area(
                    "Dirección",
                    value=company_address,
                    height=80,
                    max_chars=MAX_CHARS.get("company_address", 150)
                )
                if address_input:
                    show_char_counter("company_address", len(address_input))
            
            with col2:
                phone_input = st.text_input(
                    "Teléfono",
                    value=company_phone,
                    max_chars=MAX_CHARS.get("company_phone", 30)
                )
                if phone_input:
                    show_char_counter("company_phone", len(phone_input))
                
                email_input = st.text_input(
                    "Email",
                    value=company_email,
                    max_chars=MAX_CHARS.get("company_email", 50)
                )
                if email_input:
                    show_char_counter("company_email", len(email_input))
                
                web_input = st.text_input(
                    "Sitio web",
                    value=company_web,
                    max_chars=MAX_CHARS.get("company_web", 50)
                )
                if web_input:
                    show_char_counter("company_web", len(web_input))
            
            if st.form_submit_button("💾 Guardar Cambios", width="stretch"):
                try:
                    with SessionLocal() as db:
                        crud.set_config(db, "company_name", name_input, "company")
                        crud.set_config(db, "company_address", address_input, "company")
                        crud.set_config(db, "company_phone", phone_input, "company")
                        crud.set_config(db, "company_email", email_input, "company")
                        crud.set_config(db, "company_web", web_input, "company")
                    st.success("✅ Configuración guardada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    # Tab: Logos
    with tabs[1]:
        st.markdown("### Configuración de Logos")
        st.info("💡 Los logos aparecerán en el encabezado de las proformas (tamaño recomendado: 300x80px)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Logo Izquierdo")
            
            with SessionLocal() as db:
                current_left = crud.get_config(db, "logo_left_path", "")
            
            # Mostrar logo actual si existe
            if current_left and Path(current_left).exists():
                st.image(current_left, width=200)
                st.caption("Logo actual")
            
            # Subir nuevo logo
            logo_left_file = st.file_uploader(
                "Subir nuevo logo izquierdo",
                type=["jpg", "jpeg", "png"],
                key="logo_left"
            )
            
            if st.button("💾 Actualizar Logo Izquierdo", width="stretch"):
                if logo_left_file:
                    logo_path = save_uploaded_image(logo_left_file, prefix="logo_left")
                    if logo_path:
                        with SessionLocal() as db:
                            crud.set_config(db, "logo_left_path", logo_path, "logos")
                        st.success("✅ Logo izquierdo actualizado!")
                        st.rerun()
                else:
                    st.warning("Selecciona un archivo primero")
        
        with col2:
            st.markdown("#### Logo Derecho")
            
            with SessionLocal() as db:
                current_right = crud.get_config(db, "logo_right_path", "")
            
            # Mostrar logo actual si existe
            if current_right and Path(current_right).exists():
                st.image(current_right, width=200)
                st.caption("Logo actual")
            
            # Subir nuevo logo
            logo_right_file = st.file_uploader(
                "Subir nuevo logo derecho",
                type=["jpg", "jpeg", "png"],
                key="logo_right"
            )
            
            if st.button("💾 Actualizar Logo Derecho", width="stretch"):
                if logo_right_file:
                    logo_path = save_uploaded_image(logo_right_file, prefix="logo_right")
                    if logo_path:
                        with SessionLocal() as db:
                            crud.set_config(db, "logo_right_path", logo_path, "logos")
                        st.success("✅ Logo derecho actualizado!")
                        st.rerun()
                else:
                    st.warning("Selecciona un archivo primero")
        
        # Opción para usar logos predeterminados
        st.markdown("---")
        if st.button("🔄 Restablecer logos predeterminados"):
            with SessionLocal() as db:
                default_left = str(LOGOS_DIR / "colono.png")
                default_right = str(LOGOS_DIR / "massey.png")
                
                crud.set_config(db, "logo_left_path", default_left, "logos")
                crud.set_config(db, "logo_right_path", default_right, "logos")
            st.success("✅ Logos restablecidos!")
            st.rerun()
    
    # Tab: Términos Tractores
    with tabs[2]:
        st.markdown("### Términos y Condiciones - Tractores")
        st.info("💡 Estos términos aparecerán por defecto en proformas de tractores.")
        
        with st.form("terms_tractor_form"):
            with SessionLocal() as db:
                terms_tractor = crud.get_config(db, "terms_tractor", "")
            
            terms_input = st.text_area(
                "Términos para tractores",
                value=terms_tractor,
                height=300,
                max_chars=MAX_CHARS.get("terms_tractor", 800)
            )
            if terms_input:
                show_char_counter("terms_tractor", len(terms_input))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar", width="stretch"):
                    try:
                        with SessionLocal() as db:
                            crud.set_config(db, "terms_tractor", terms_input, "tractor")
                        st.success("✅ Términos guardados!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            with col2:
                if st.form_submit_button("📄 Restablecer", width="stretch"):
                    from app.config_defaults import DEFAULT_CONFIG
                    try:
                        with SessionLocal() as db:
                            crud.set_config(db, "terms_tractor", DEFAULT_CONFIG["terms_tractor"], "tractor")
                        st.success("✅ Términos restablecidos!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    # Tab: Términos Implementos
    with tabs[3]:
        st.markdown("### Términos y Condiciones - Implementos")
        st.info("💡 Estos términos aparecerán por defecto en proformas de implementos.")
        
        with st.form("terms_implement_form"):
            with SessionLocal() as db:
                terms_implement = crud.get_config(db, "terms_implement", "")
            
            terms_input = st.text_area(
                "Términos para implementos",
                value=terms_implement,
                height=300,
                max_chars=MAX_CHARS.get("terms_implement", 800)
            )
            if terms_input:
                show_char_counter("terms_implement", len(terms_input))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar", width="stretch"):
                    try:
                        with SessionLocal() as db:
                            crud.set_config(db, "terms_implement", terms_input, "implement")
                        st.success("✅ Términos guardados!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            with col2:
                if st.form_submit_button("📄 Restablecer", width="stretch"):
                    from app.config_defaults import DEFAULT_CONFIG
                    try:
                        with SessionLocal() as db:
                            crud.set_config(db, "terms_implement", DEFAULT_CONFIG["terms_implement"], "implement")
                        st.success("✅ Términos restablecidos!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    # Tab: Nota Fiscal
    with tabs[4]:
        st.markdown("### Nota Fiscal")
        st.info("💡 Esta nota aparecerá en el footer de todas las proformas.")
        
        with st.form("fiscal_note_form"):
            with SessionLocal() as db:
                fiscal_note = crud.get_config(db, "fiscal_note", "")
            
            note_input = st.text_area(
                "Nota fiscal",
                value=fiscal_note,
                height=200,
                max_chars=MAX_CHARS.get("fiscal_note", 400)
            )
            if note_input:
                show_char_counter("fiscal_note", len(note_input))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar", width="stretch"):
                    try:
                        with SessionLocal() as db:
                            crud.set_config(db, "fiscal_note", note_input, "general")
                        st.success("✅ Nota fiscal guardada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            with col2:
                if st.form_submit_button("📄 Restablecer", width="stretch"):
                    from app.config_defaults import DEFAULT_CONFIG
                    try:
                        with SessionLocal() as db:
                            crud.set_config(db, "fiscal_note", DEFAULT_CONFIG["fiscal_note"], "general")
                        st.success("✅ Nota fiscal restablecida!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")


# ========================= FOOTER =========================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>🚜 <strong>AgriQuote v2.0</strong> - Sistema de Cotizaciones Agrícolas</p>
        <p>© 2025 Colono - Todos los derechos reservados</p>
    </div>
    """,
    unsafe_allow_html=True
)