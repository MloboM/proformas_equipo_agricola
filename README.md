# 🚜 AgriQuote - Sistema de Cotizaciones Agrícolas

Sistema profesional para la gestión y generación de cotizaciones de equipos agrícolas (tractores e implementos).

## 📋 Características

### ✨ Funcionalidades Principales

- **Gestión de Productos**
  - Crear, editar y eliminar equipos
  - Soporte para tractores e implementos
  - Carga de imágenes de productos
  - Especificaciones técnicas detalladas
  - Control de estado (activo/inactivo)

- **Generación de Proformas**
  - Dos plantillas profesionales (tractores/implementos)
  - Soporte multi-moneda (CRC/USD)
  - Cálculo automático de impuestos (13% IVA)
  - PDFs con diseño profesional
  - Múltiples productos por cotización

- **Personalización**
  - Términos y condiciones personalizables
  - Datos de empresa configurables
  - Información de asesores
  - Vigencia de cotizaciones

### 🎨 Interfaz de Usuario

- Diseño moderno y responsivo
- Navegación intuitiva por pestañas
- Validación de formularios en tiempo real
- Mensajes de éxito/error claros
- Vista previa de términos y condiciones

## 🛠️ Tecnologías

- **Backend**: Python 3.8+
- **Framework UI**: Streamlit
- **Base de datos**: SQLite con SQLAlchemy
- **Validación**: Pydantic
- **PDFs**: ReportLab
- **Imágenes**: Pillow

## 📦 Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd AgriQuote
   ```

2. **Crear entorno virtual** (recomendado)
   ```bash
   python -m venv .venv
   ```

3. **Activar entorno virtual**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Crear estructura de directorios**
   ```bash
   mkdir -p data media/uploads media/logos media/fonts outputs
   ```

6. **Agregar recursos** (opcional pero recomendado)
   - Colocar logos en `media/logos/`:
     - `colono.png`
     - `massey.png` (para tractores)
   - Colocar fuente en `media/fonts/`:
     - `DejaVuSans.ttf` (para símbolo ₡)

## 🚀 Uso

### Ejecutar la aplicación

```bash
streamlit run streamlit_app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Flujo de Trabajo

1. **Configurar Productos**
   - Ir a "📦 Gestión de Equipos"
   - Crear productos con sus especificaciones
   - Subir imágenes de los equipos

2. **Personalizar Términos** (opcional)
   - Ir a "⚙️ Configuración"
   - Editar términos por tipo de plantilla

3. **Generar Cotizaciones**
   - Ir a "🆕 Nueva Proforma"
   - Completar datos del cliente
   - Seleccionar productos
   - Configurar precios y cantidades
   - Generar PDF

## 📁 Estructura del Proyecto

```
AgriQuote/
├── app/
│   ├── __init__.py          # Inicialización del módulo
│   ├── db.py                # Configuración de base de datos
│   ├── models.py            # Modelos de datos principales
│   ├── models_terms.py      # Modelo de términos
│   ├── schemas.py           # Esquemas de validación Pydantic
│   ├── crud.py              # Operaciones CRUD
│   └── pdf.py               # Generación de PDFs
├── data/
│   └── agriquote.db         # Base de datos SQLite (auto-generada)
├── media/
│   ├── fonts/               # Fuentes para PDFs
│   ├── logos/               # Logos de la empresa
│   ├── uploads/             # Imágenes de productos
│   └── products/            # Imágenes adicionales
├── outputs/                 # PDFs generados
├── streamlit_app.py         # Aplicación principal
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## 🔧 Configuración

### Base de Datos

La base de datos SQLite se crea automáticamente en `data/agriquote.db`. No requiere configuración adicional.

### Recursos Opcionales

1. **Logos**: Colocar en `media/logos/`
   - `colono.png`: Logo principal (110x28px recomendado)
   - `massey.png`: Logo de Massey Ferguson para tractores

2. **Fuente Unicode**: Para símbolo de colón (₡)
   - Descargar DejaVuSans.ttf
   - Colocar en `media/fonts/`

## 📊 Base de Datos

### Tablas

- **products**: Equipos y productos
- **proformas**: Cotizaciones generadas
- **proforma_items**: Items de cada cotización
- **terms**: Términos y condiciones por plantilla

### Backup

```bash
# Respaldar base de datos
cp data/agriquote.db data/agriquote_backup.db
```

## 🎯 Características Avanzadas

### Multi-moneda

- Soporta CRC (Colones) y USD (Dólares)
- Cálculos separados por moneda
- Conversión automática no incluida

### Plantillas de PDF

- **Tractor**: Incluye campo "Año"
- **Implemento**: Sin campo año, enfoque en especificaciones

### Validaciones

- Campos obligatorios marcados con *
- Validación de emails
- Precios no negativos
- Cantidades mínimas

## 🐛 Solución de Problemas

### La aplicación no inicia

```bash
# Verificar instalación de dependencias
pip install -r requirements.txt --upgrade
```

### Error de base de datos

```bash
# Eliminar y recrear base de datos
rm data/agriquote.db
# La base se recreará automáticamente al iniciar
```

### Imágenes no se muestran en PDF

- Verificar que las rutas de imagen sean correctas
- Asegurarse de que los archivos existen en `media/uploads/`
- Formatos soportados: JPG, PNG, GIF

### Símbolo ₡ no aparece

- Instalar fuente DejaVuSans.ttf en `media/fonts/`
- Alternativamente, se usará "CRC" como prefijo

## 🔒 Seguridad

- **No** usar en producción sin medidas adicionales
- Base de datos sin encriptación
- Sin autenticación de usuarios
- Pensado para uso interno/local

## 📝 Próximas Mejoras

- [ ] Exportar a Excel
- [ ] Historial de cotizaciones
- [ ] Búsqueda avanzada
- [ ] Plantillas personalizadas
- [ ] Sistema de usuarios
- [ ] Envío de emails
- [ ] Conversión de monedas
- [ ] Reportes y estadísticas

## 🤝 Contribuciones

Este proyecto está en desarrollo activo. Sugerencias y mejoras son bienvenidas.

## 📄 Licencia

Uso interno para Colono. Todos los derechos reservados.

## 📞 Soporte

Para consultas o soporte, contactar al equipo de desarrollo.

---

**Versión**: 1.0.0  
**Última actualización**: 2025

🚜 Hecho con ❤️ para la industria agrícola