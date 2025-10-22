"""
Generación de PDFs para proformas con paginación automática - VERSIÓN MEJORADA
"""
from pathlib import Path
from typing import List, Dict, Optional
import textwrap

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ==================== CONFIGURACIÓN ====================

PAGE_W, PAGE_H = letter
MARGIN_LEFT = 0.6 * inch
MARGIN_RIGHT = 0.6 * inch
MARGIN_TOP = 0.7 * inch
MARGIN_BOTTOM = 0.7 * inch
CONTENT_WIDTH = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

# Altura fija del header (aumentada 15% para logos más grandes)
HEADER_HEIGHT = 1.15 * inch

# Altura fija del footer
FOOTER_HEIGHT = 2.1 * inch

# Altura disponible para contenido dinámico
DYNAMIC_HEIGHT = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM - HEADER_HEIGHT - FOOTER_HEIGHT

# Rutas de recursos
MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
LOGOS_DIR = MEDIA_DIR / "logos"
FONTS_DIR = MEDIA_DIR / "fonts"
UPLOAD_DIR = MEDIA_DIR / "uploads"

# Configuración de fuentes
FONT_TTF = FONTS_DIR / "DejaVuSans.ttf"
USE_UNICODE = False

try:
    if FONT_TTF.exists():
        pdfmetrics.registerFont(TTFont("DejaVuSans", str(FONT_TTF)))
        FONT_NORMAL = "DejaVuSans"
        FONT_BOLD = "DejaVuSans-Bold"
        USE_UNICODE = True
    else:
        FONT_NORMAL = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"
except Exception:
    FONT_NORMAL = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

# Colores corporativos
COLOR_PRIMARY = colors.HexColor("#2E7D32")
COLOR_SECONDARY = colors.HexColor("#66BB6A")
COLOR_BORDER = colors.HexColor("#9AB8A3")
COLOR_BG_LIGHT = colors.HexColor("#F1F8F4")

# Estilos de texto
_base_styles = getSampleStyleSheet()

STYLE_TINY = ParagraphStyle(
    "Tiny", parent=_base_styles["Normal"],
    fontName=FONT_NORMAL, fontSize=6.5, leading=8
)

STYLE_SMALL = ParagraphStyle(
    "Small", parent=_base_styles["Normal"],
    fontName=FONT_NORMAL, fontSize=7.5, leading=9.5
)

STYLE_NORMAL = ParagraphStyle(
    "Normal", parent=_base_styles["Normal"],
    fontName=FONT_NORMAL, fontSize=9, leading=11
)


# ==================== UTILIDADES ====================

def currency_symbol(currency: str) -> str:
    """Retorna el símbolo de moneda"""
    if currency == "USD":
        return "$"
    if currency == "CRC":
        return "₡" if USE_UNICODE else "CRC "
    return f"{currency} "


def format_money(amount: float, currency: str) -> str:
    """Formatea un monto con su moneda"""
    symbol = currency_symbol(currency)
    return f"{symbol}{amount:,.2f}"


def truncate_text(text: str, max_chars: int) -> str:
    """Trunca texto al límite de caracteres"""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def wrap_text(text: str, width: int = 85) -> List[str]:
    """Divide texto en líneas"""
    if not text:
        return []
    
    lines = []
    for paragraph in text.splitlines():
        if paragraph.strip():
            lines.extend(textwrap.wrap(paragraph, width=width))
        else:
            lines.append("")
    return lines


def draw_soft_line(c: canvas.Canvas, x1: float, y1: float, 
                   x2: float, y2: float, width: float = 0.6):
    """Dibuja una línea suave"""
    c.saveState()
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    c.restoreState()


# ==================== SECCIÓN FIJA: HEADER ====================

def draw_header(c: canvas.Canvas, data: Dict, template: str):
    """Dibuja el header fijo con logos configurables (tamaño aumentado 15%)"""
    
    y_start = PAGE_H - MARGIN_TOP
    
    # Logo izquierdo (configurable)
    logo_left_path = data.get("logo_left_path")
    if logo_left_path and Path(logo_left_path).exists():
        try:
            logo = ImageReader(str(logo_left_path))
            c.drawImage(
                logo, MARGIN_LEFT, y_start - 32,
                width=127, height=32,  # Aumentado 15%
                preserveAspectRatio=True, mask='auto'
            )
        except Exception:
            pass
    
    # Logo derecho (configurable)
    logo_right_path = data.get("logo_right_path")
    if logo_right_path and Path(logo_right_path).exists():
        try:
            logo = ImageReader(str(logo_right_path))
            c.drawImage(
                logo, PAGE_W - MARGIN_RIGHT - 127, y_start - 32,
                width=127, height=32,  # Aumentado 15%
                preserveAspectRatio=True, mask='auto'
            )
        except Exception:
            pass
    
    # Línea decorativa
    y_line = y_start - 40
    c.setStrokeColor(COLOR_PRIMARY)
    c.setLineWidth(1.5)
    c.line(MARGIN_LEFT, y_line, PAGE_W - MARGIN_RIGHT, y_line)
    
    # Información de la empresa (lado izquierdo)
    c.setFillColor(colors.black)
    c.setFont(FONT_NORMAL, 8)

    y_info_left = y_line - 15  # misma altura inicial que el bloque derecho
    x_info_left = MARGIN_LEFT  # margen izquierdo de la página

    # Línea 1: Nombre de la empresa
    c.drawString(x_info_left, y_info_left, "Colono Agropecuario S. A.")
    y_info_left -= 12

    # Línea 2: Cédula jurídica
    c.drawString(x_info_left, y_info_left, "Cédula Jurídica: 3 101 268981")
    y_info_left -= 12

    # Línea 3: Teléfono
    c.drawString(x_info_left, y_info_left, "Teléfono: (506) 2799-6120")
    y_info_left -= 12

    # Línea 4: WhatsApp
    c.drawString(x_info_left, y_info_left, "Whatsapp: (506) 7007-1200")
    y_info_left -= 12

    
    # Información de la empresa (lado derecho)
    c.setFillColor(colors.black)
    c.setFont(FONT_NORMAL, 8)
    
    y_info = y_line - 15
    
    company_addr = truncate_text(data.get("company_address", ""), 150)
    if company_addr:
        c.drawRightString(PAGE_W - MARGIN_RIGHT, y_info, company_addr)
        y_info -= 12
    
    company_contacts = []
    if data.get("company_phone"):
        company_contacts.append(f"Tel: {truncate_text(data.get('company_phone'), 30)}")
    if data.get("company_email"):
        company_contacts.append(truncate_text(data.get("company_email"), 50))
    if data.get("company_web"):
        company_contacts.append(truncate_text(data.get("company_web"), 50))
    
    if company_contacts:
        c.drawRightString(PAGE_W - MARGIN_RIGHT, y_info, " | ".join(company_contacts))
        y_info -= 12
    
    # Fecha
    c.setFont(FONT_NORMAL, 9)
    c.drawRightString(PAGE_W - MARGIN_RIGHT, y_info, f"Fecha: {data.get('date', '')}")
    y_info -= 12
    
    # Cotización y Número en la misma línea
    c.setFont(FONT_BOLD, 9)
    c.drawRightString(PAGE_W - MARGIN_RIGHT, y_info, f"N°: {data.get('number', '')}")
    num_width = c.stringWidth(f"N°: {data.get('number', '')}", FONT_BOLD, 9)
    c.drawRightString(PAGE_W - MARGIN_RIGHT - num_width - 5, y_info, "Cotización:")


# ==================== SECCIÓN FIJA: FOOTER MEJORADO ====================

def draw_footer(c: canvas.Canvas, data: Dict, totals: Optional[Dict], 
                template: str, is_last_page: bool = False):
    """Dibuja el footer reorganizado sin superposiciones"""
    
    y_end = MARGIN_BOTTOM
    y_start = y_end + FOOTER_HEIGHT
    
    # Fondo con color
    c.setFillColor(COLOR_BG_LIGHT)
    c.setStrokeColor(COLOR_PRIMARY)
    c.setLineWidth(1.5)
    c.roundRect(MARGIN_LEFT, y_end, CONTENT_WIDTH, FOOTER_HEIGHT, 10, stroke=1, fill=1)
    
    # Nueva distribución de columnas
    if is_last_page and totals:
        # Con totales: 3 columnas
        col1_width = CONTENT_WIDTH * 0.22  # Vigencia y Asesor
        col2_width = CONTENT_WIDTH * 0.48  # Condiciones y Nota
        col3_width = CONTENT_WIDTH * 0.30  # Totales
    else:
        # Sin totales: 2 columnas más amplias
        col1_width = CONTENT_WIDTH * 0.25
        col2_width = CONTENT_WIDTH * 0.75
        col3_width = 0
    
    col1_x = MARGIN_LEFT + 8
    col2_x = MARGIN_LEFT + col1_width + 8
    col3_x = PAGE_W - MARGIN_RIGHT - col3_width - 8 if col3_width > 0 else 0
    
    # Líneas divisorias
    draw_soft_line(c, MARGIN_LEFT + col1_width, y_end, MARGIN_LEFT + col1_width, y_start)
    if col3_width > 0:
        draw_soft_line(c, PAGE_W - MARGIN_RIGHT - col3_width, y_end, 
                       PAGE_W - MARGIN_RIGHT - col3_width, y_start)
    
    # COLUMNA 1: Vigencia y Asesor (más compacto)
    c.setFillColor(COLOR_PRIMARY)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(col1_x, y_start - 14, "VIGENCIA")
    
    c.setFillColor(colors.black)
    c.setFont(FONT_NORMAL, 7.5)
    validity = data.get("validity_days", 15)
    c.drawString(col1_x, y_start - 26, f"{validity} días")
    
    # Asesor
    y_advisor = y_start - 42
    c.setFillColor(COLOR_PRIMARY)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(col1_x, y_advisor, "ASESOR")
    
    c.setFillColor(colors.black)
    c.setFont(FONT_NORMAL, 7)
    advisor_name = truncate_text(data.get("advisor_name", ""), 28)
    if advisor_name:
        c.drawString(col1_x, y_advisor - 12, advisor_name)
    
    advisor_phone = truncate_text(data.get("advisor_phone", ""), 20)
    if advisor_phone:
        c.drawString(col1_x, y_advisor - 22, f"Tel: {advisor_phone}")
    
    advisor_email = truncate_text(data.get("advisor_email", ""), 28)
    if advisor_email:
        c.setFont(FONT_NORMAL, 6.5)
        c.drawString(col1_x, y_advisor - 32, advisor_email)
    
    # COLUMNA 2: Condiciones y Nota Fiscal (sin superposición)
    c.setFillColor(COLOR_PRIMARY)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(col2_x, y_start - 14, "CONDICIONES")
    
    # Usar 55% del espacio para condiciones
    c.setFillColor(colors.black)
    terms_text = truncate_text(data.get("terms", ""), 500)
    if terms_text:
        para = Paragraph(terms_text.replace("\n", "<br/>"), STYLE_TINY)
        w, h = para.wrap(col2_width - 10, FOOTER_HEIGHT * 0.50)
        para.drawOn(c, col2_x, y_start - 20 - h)
    
    # Nota fiscal en el 45% restante
    y_fiscal = y_start - (FOOTER_HEIGHT * 0.55)
    c.setFillColor(COLOR_PRIMARY)
    c.setFont(FONT_BOLD, 7.5)
    c.drawString(col2_x, y_fiscal, "NOTA FISCAL")
    
    c.setFillColor(colors.black)
    fiscal_text = truncate_text(data.get("fiscal_note", ""), 250)
    if fiscal_text:
        para = Paragraph(fiscal_text.replace("\n", "<br/>"), STYLE_TINY)
        w, h = para.wrap(col2_width - 10, FOOTER_HEIGHT * 0.35)
        para.drawOn(c, col2_x, y_fiscal - 8 - h)
    
    # COLUMNA 3: Totales (solo en última página)
    if is_last_page and totals and col3_width > 0:
        c.setFillColor(COLOR_PRIMARY)
        c.setFont(FONT_BOLD, 9.5)
        c.drawString(col3_x, y_start - 14, "TOTALES")
        
        y_totals = y_start - 30
        c.setFillColor(colors.black)
        
        if "subtotal" in totals:
            # Una sola moneda
            cur = totals.get("currency", "CRC")
            c.setFont(FONT_NORMAL, 8)
            
            # Subtotal
            c.drawString(col3_x, y_totals, "Subtotal:")
            c.drawRightString(col3_x + col3_width - 10, y_totals, 
                            format_money(totals["subtotal"], cur))
            y_totals -= 12
            
            # Descuento (si existe)
            if totals.get("discount", 0) > 0:
                c.drawString(col3_x, y_totals, "Descuento:")
                c.drawRightString(col3_x + col3_width - 10, y_totals,
                                format_money(totals["discount"], cur))
                y_totals -= 12
            
            # IVA con porcentaje personalizado
            tax_rate = totals.get("tax_rate", 13)
            c.drawString(col3_x, y_totals, f"IVA {tax_rate}%:")
            c.drawRightString(col3_x + col3_width - 10, y_totals,
                            format_money(totals["tax"], cur))
            y_totals -= 14
            
            # Total
            c.setFont(FONT_BOLD, 9)
            c.drawString(col3_x, y_totals, "TOTAL:")
            c.drawRightString(col3_x + col3_width - 10, y_totals,
                            format_money(totals["total"], cur))
        else:
            # Múltiples monedas
            for cur in sorted(totals.keys()):
                if cur in ("CRC", "USD"):
                    t = totals[cur]
                    c.setFont(FONT_BOLD, 8)
                    c.drawString(col3_x, y_totals, f"{cur}:")
                    y_totals -= 10
                    
                    c.setFont(FONT_NORMAL, 7)
                    c.drawString(col3_x + 3, y_totals, "Sub:")
                    c.drawRightString(col3_x + col3_width - 10, y_totals,
                                    format_money(t["subtotal"], cur))
                    y_totals -= 8
                    
                    if t.get("discount", 0) > 0:
                        c.drawString(col3_x + 3, y_totals, "Desc:")
                        c.drawRightString(col3_x + col3_width - 10, y_totals,
                                        format_money(t["discount"], cur))
                        y_totals -= 8
                    
                    tax_rate = t.get("tax_rate", 13)
                    c.drawString(col3_x + 3, y_totals, f"IVA {tax_rate}%:")
                    c.drawRightString(col3_x + col3_width - 10, y_totals,
                                    format_money(t["tax"], cur))
                    y_totals -= 8
                    
                    c.setFont(FONT_BOLD, 7.5)
                    c.drawString(col3_x, y_totals, "Total:")
                    c.drawRightString(col3_x + col3_width - 10, y_totals,
                                    format_money(t["total"], cur))
                    y_totals -= 12


# ==================== SECCIÓN: DATOS DEL CLIENTE (COMPACTO) ====================

def draw_customer_section(c: canvas.Canvas, data: Dict, y_start: float):
    """Dibuja la sección de datos del cliente en formato compacto de una línea"""
    
    section_height = 35  # Reducido significativamente
    y_end = y_start - section_height
    
    # --- Ajustes de padding y posición ---
    top_padding = 6       # Espacio adicional arriba del texto
    x_offset = -5         # Desplazamiento horizontal hacia la izquierda (puedes ajustar a gusto)
    
    # Marco
    #c.setStrokeColor(COLOR_BORDER)
    #c.setLineWidth(1)
    #c.rect(MARGIN_LEFT, y_end, CONTENT_WIDTH, section_height)
    
    # Título
    c.setFillColor(COLOR_PRIMARY)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(MARGIN_LEFT + 8 + x_offset, y_start - 12- top_padding, "CLIENTE:")
    
    # Datos en línea continua
    c.setFillColor(colors.black)
    c.setFont(FONT_NORMAL, 8)
    
    x_pos = MARGIN_LEFT + 60 + x_offset
    y_pos = y_start - 12 - top_padding
    
    # Construir línea de información
    info_parts = []
    
    customer_name = truncate_text(data.get("customer_name", ""), 40)
    if customer_name:
        info_parts.append(customer_name)
    
    customer_company = truncate_text(data.get("customer_company", ""), 35)
    if customer_company:
        info_parts.append(f"({customer_company})")
    
    customer_attention = truncate_text(data.get("customer_attention", ""), 30)
    if customer_attention:
        info_parts.append(f"Att: {customer_attention}")
    
    customer_email = truncate_text(data.get("customer_email", ""), 35)
    if customer_email:
        info_parts.append(customer_email)
    
    customer_phone = truncate_text(data.get("customer_phone", ""), 20)
    if customer_phone:
        info_parts.append(f"Tel: {customer_phone}")
    
    # Segunda línea si hay dirección
    line1 = " | ".join(info_parts[:4])  # Primeros 4 elementos
    c.drawString(x_pos, y_pos, line1)
    
    if len(info_parts) > 4 or data.get("customer_address"):
        y_pos -= 10
        line2_parts = info_parts[4:]
        
        customer_address = truncate_text(data.get("customer_address", ""), 60)
        if customer_address:
            line2_parts.append(customer_address)
        
        if line2_parts:
            c.drawString(x_pos, y_pos, " | ".join(line2_parts))
    
    return section_height


# ==================== SECCIÓN DINÁMICA: PRODUCTO (MEJORADO) ====================

def draw_product_content(c: canvas.Canvas, item: Dict, template: str, y_start: float):
    """Dibuja el contenido dinámico de un producto con mejor alineación"""
    
    # Configuración de tabla
    table_row_height = 18
    
    # Definir columnas según template - ANCHOS OPTIMIZADOS
    if template == "tractor":
        columns = [
            ("CANT.", 0.45*inch),
            ("MARCA", 1.0*inch),
            ("MODELO", 1.6*inch),
            ("AÑO", 0.45*inch),
            ("P. UNIT", 1.4*inch),
            ("DESC%", 0.55*inch),
            ("IVA%", 0.45*inch),
            ("TOTAL", 1.5*inch),
        ]
    else:
        columns = [
            ("CANT.", 0.5*inch),
            ("MARCA", 1.2*inch),
            ("MODELO", 1.9*inch),
            ("P. UNIT", 1.4*inch),
            ("DESC%", 0.55*inch),
            ("IVA%", 0.45*inch),
            ("TOTAL", 1.5*inch),
        ]
    
    # Header de tabla
    y_table_header = y_start
    c.setStrokeColor(COLOR_BORDER)
    c.setFillColor(COLOR_BG_LIGHT)
    c.rect(MARGIN_LEFT, y_table_header - table_row_height, 
           CONTENT_WIDTH, table_row_height, fill=1)
    
    c.setFillColor(COLOR_PRIMARY)
    c.setFont(FONT_BOLD, 8)
    
    x = MARGIN_LEFT
    for col_name, col_width in columns:
        if col_name in ("P. UNIT", "TOTAL"):
            # Alinear a la derecha los títulos de columnas de montos
            c.drawRightString(x + col_width - 10, y_table_header - 12, col_name)
        else:
            c.drawString(x + 3, y_table_header - 12, col_name)
        x += col_width
    
    # Líneas verticales del header
    x = MARGIN_LEFT
    for _, col_width in columns[:-1]:
        x += col_width
        draw_soft_line(c, x, y_table_header - table_row_height, x, y_table_header)
    
    # Fila de datos
    y_table_data = y_table_header - table_row_height
    c.setStrokeColor(COLOR_BORDER)
    c.setFillColor(colors.white)
    c.rect(MARGIN_LEFT, y_table_data - table_row_height, 
           CONTENT_WIDTH, table_row_height, fill=1)
    
    c.setFillColor(colors.black)
    c.setFont(FONT_NORMAL, 8)
    
    # Preparar valores
    if template == "tractor":
        values = [
            str(item.get("qty", 0)),
            truncate_text(item.get("brand_name", ""), 14),
            truncate_text(item.get("model_name", ""), 22),
            str(item.get("year", "") or ""),
            format_money(item.get("unit_price", 0), item.get("currency", "CRC")),
            f"{item.get('discount_percent', 0):.1f}%" if item.get('discount_percent', 0) > 0 else "-",
            f"{item.get('tax_rate', 13)}%",
            format_money(item.get("line_total", 0), item.get("currency", "CRC")),
        ]
    else:
        values = [
            str(item.get("qty", 0)),
            truncate_text(item.get("brand_name", ""), 18),
            truncate_text(item.get("model_name", ""), 28),
            format_money(item.get("unit_price", 0), item.get("currency", "CRC")),
            f"{item.get('discount_percent', 0):.1f}%" if item.get('discount_percent', 0) > 0 else "-",
            f"{item.get('tax_rate', 13)}%",
            format_money(item.get("line_total", 0), item.get("currency", "CRC")),
        ]
    
    # Dibujar valores con alineación correcta
    x = MARGIN_LEFT
    y_text = y_table_data - 12
    
    for (col_name, col_width), value in zip(columns, values):
        if col_name in ("P. UNIT", "TOTAL"):
            # ALINEACIÓN A LA DERECHA PARA MONTOS
            c.drawRightString(x + col_width - 10, y_text, value)
        elif col_name in ("CANT.", "AÑO", "DESC%", "IVA%"):
            # Centrado para valores numéricos cortos
            c.drawCentredString(x + col_width / 2, y_text, value)
        else:
            # Alineación a la izquierda para texto
            c.drawString(x + 3, y_text, value)
        x += col_width
    
    # Líneas verticales de la fila de datos
    x = MARGIN_LEFT
    for _, col_width in columns[:-1]:
        x += col_width
        draw_soft_line(c, x, y_table_data - table_row_height, x, y_table_data)
    
    # Especificaciones técnicas (resto igual)
    y_specs_start = y_table_data - table_row_height - 10
    specs_height = DYNAMIC_HEIGHT - (table_row_height * 2) - 20
    y_specs_end = y_specs_start - specs_height
    
    # Marco de especificaciones
    c.setStrokeColor(COLOR_BORDER)
    c.rect(MARGIN_LEFT, y_specs_end, CONTENT_WIDTH, specs_height)
    
    # División vertical
    specs_text_width = CONTENT_WIDTH * 0.58
    specs_image_width = CONTENT_WIDTH * 0.38
    split_x = MARGIN_LEFT + specs_text_width + (CONTENT_WIDTH * 0.04)
    
    draw_soft_line(c, split_x, y_specs_end, split_x, y_specs_start)
    
    # Título
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(COLOR_PRIMARY)
    c.drawString(MARGIN_LEFT + 8, y_specs_start - 14, "Especificaciones Técnicas")
    
    # Texto de especificaciones
    c.setFillColor(colors.black)
    c.setFont(FONT_NORMAL, 8.5)
    description = truncate_text(item.get("description", ""), 1000)
    
    y_text = y_specs_start - 28
    for line in wrap_text(description, width=75):
        if y_text < (y_specs_end + 10):
            break
        c.drawString(MARGIN_LEFT + 8, y_text, line)
        y_text -= 11
    
    # Imagen - CENTRADA VERTICAL Y HORIZONTALMENTE
    image_margin = 10
    top_padding = 15
    
    image_x = split_x + image_margin
    image_y = y_specs_end + image_margin
    image_width = specs_image_width - (2 * image_margin)
    image_height = specs_height - (2 * image_margin)
    
    image_path = item.get("image_path")
    if image_path and Path(image_path).exists():
        try:
            img = ImageReader(str(image_path))
            img_w, img_h = img.getSize()
            
            scale = min(image_width / img_w, image_height / img_h)
            scaled_w = img_w * scale
            scaled_h = img_h * scale
            
            centered_x = image_x + (image_width - scaled_w) / 2
            centered_y = image_y + image_height - scaled_h - top_padding
            #centered_y = image_y + (image_height - scaled_h) / 2
            
            c.drawImage(
                img, centered_x, centered_y,
                width=scaled_w,
                height=scaled_h,
                preserveAspectRatio=True
            )
        except Exception:
            c.setFont(FONT_NORMAL, 9)
            c.setFillColor(colors.grey)
            c.drawString(image_x + image_width/2 - 40, image_y + image_height / 2, "(Imagen no disponible)")
    else:
        c.setFont(FONT_NORMAL, 9)
        c.setFillColor(colors.grey)
        c.drawString(image_x + image_width/2 - 30, image_y + image_height / 2, "(Sin imagen)")


# ==================== FUNCIÓN PRINCIPAL ====================

def build_proforma_pdf(
    output_path: Path,
    header_data: Dict,
    items: List[Dict],
    totals: Optional[Dict],
    template: str = "implement"
) -> Path:
    """
    Genera un PDF de proforma con paginación automática mejorado
    """
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Calcular posición inicial del contenido dinámico
    y_dynamic_start = PAGE_H - MARGIN_TOP - HEADER_HEIGHT - 10
    
    for idx, item in enumerate(items):
        is_first_page = (idx == 0)
        is_last_page = (idx == len(items) - 1)
        
        # Dibujar header (siempre)
        draw_header(c, header_data, template)
        
        # En primera página: dibujar datos del cliente (más compacto)
        if is_first_page:
            customer_height = draw_customer_section(c, header_data, y_dynamic_start)
            y_product_start = y_dynamic_start - customer_height - 10
        else:
            y_product_start = y_dynamic_start
        
        # Dibujar contenido del producto
        draw_product_content(c, item, template, y_product_start)
        
        # Dibujar footer (siempre, pero totales solo en última página)
        draw_footer(c, header_data, totals, template, is_last_page)
        
        # Nueva página si no es la última
        if not is_last_page:
            c.showPage()
    
    # Guardar PDF
    c.save()
    return output_path