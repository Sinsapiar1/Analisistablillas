import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración de la página
st.set_page_config(
    page_title="📦 Visor de Inventario Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado y JavaScript mejorado
st.markdown("""
<style>
    /* Estilos principales mejorados */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .input-section {
        background: rgba(0, 123, 255, 0.05);
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        transition: all 0.3s ease;
    }
    
    .input-section.active {
        border-color: #007bff;
        background: rgba(0, 123, 255, 0.1);
        box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
    }
    
    .success-alert {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #155724;
    }
    
    .executive-dashboard {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    /* Animaciones para feedback visual */
    @keyframes pulse-success {
        0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
    }
    
    .field-success {
        animation: pulse-success 1s;
    }
    
    /* Estilos para tablas mejoradas */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Indicadores de estado mejorados */
    .status-exact { color: #28a745; font-weight: bold; }
    .status-over { color: #fd7e14; font-weight: bold; }
    .status-under { color: #dc3545; font-weight: bold; }
    .status-missing { color: #6f42c1; font-weight: bold; }
    
    /* Instrucciones de navegación */
    .keyboard-instructions {
        background: linear-gradient(135deg, #e8f5e8, #d4edda);
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        text-align: center;
        font-weight: bold;
        color: #155724;
    }
</style>

<script>
// Sistema de navegación por teclado mejorado
let currentFieldIndex = 0;
let fields = [];
let isProcessing = false;

function initializeKeyboardNavigation() {
    // Obtener todos los campos de entrada visibles
    fields = Array.from(document.querySelectorAll('input[type="text"], input[type="number"]'))
        .filter(input => input.offsetParent !== null);
    
    // Configurar eventos para cada campo
    fields.forEach((field, index) => {
        field.removeEventListener('keydown', handleKeyDown);
        field.addEventListener('keydown', handleKeyDown);
        field.setAttribute('data-field-index', index);
    });
    
    // Auto-focus en el primer campo
    if (fields.length > 0 && !isProcessing) {
        setTimeout(() => {
            fields[0].focus();
            fields[0].select();
            currentFieldIndex = 0;
        }, 100);
    }
}

function handleKeyDown(e) {
    const currentField = e.target;
    const fieldIndex = parseInt(currentField.getAttribute('data-field-index'));
    
    if (e.key === 'Enter') {
        e.preventDefault();
        
        if (fieldIndex === fields.length - 1) {
            // Último campo (cantidad) - activar botón agregar
            const addButton = document.querySelector('button[kind="primary"]');
            if (addButton && addButton.textContent.includes('Agregar')) {
                isProcessing = true;
                addButton.click();
                
                // Después de agregar, esperar y re-enfocar
                setTimeout(() => {
                    isProcessing = false;
                    initializeKeyboardNavigation();
                }, 500);
            }
        } else {
            // Ir al siguiente campo
            const nextField = fields[fieldIndex + 1];
            if (nextField) {
                nextField.focus();
                nextField.select();
                currentFieldIndex = fieldIndex + 1;
            }
        }
    }
}

// Inicializar cuando la página se carga
document.addEventListener('DOMContentLoaded', initializeKeyboardNavigation);

// Re-inicializar después de actualizaciones de Streamlit
const observer = new MutationObserver((mutations) => {
    let shouldReinit = false;
    mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            shouldReinit = true;
        }
    });
    
    if (shouldReinit && !isProcessing) {
        setTimeout(initializeKeyboardNavigation, 100);
    }
});

observer.observe(document.body, { 
    childList: true, 
    subtree: true 
});
</script>
""", unsafe_allow_html=True)

# Inicializar estado de la sesión con mejoras
def init_session_state():
    """Inicializar estado de sesión con configuración optimizada"""
    defaults = {
        'inventario_sistema': None,
        'conteo_fisico': [],
        'archivo_cargado': False,
        'campo_counter': 0,
        'last_added_id': None,
        'session_stats': {
            'start_time': datetime.now(),
            'total_processed': 0,
        }
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# Función para limpiar memoria en Streamlit Cloud
def cleanup_memory():
    """Limpia memoria para evitar problemas en Streamlit Cloud"""
    import gc
    gc.collect()

# Funciones auxiliares mejoradas
def cargar_inventario(archivo):
    """Carga y valida el archivo de inventario con mejor manejo de errores"""
    try:
        with st.spinner("Cargando y validando archivo..."):
            # Leer archivo Excel con mejor manejo
            df = pd.read_excel(archivo, dtype=str, engine='openpyxl')
            
            # Limpiar y normalizar
            df = df.dropna(how='all')  # Eliminar filas completamente vacías
            df.columns = [str(c).strip() for c in df.columns]
            
            # Validar columnas requeridas
            required_cols = ['Id de pallet', 'Inventario físico']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Columnas requeridas faltantes: {', '.join(missing_cols)}")
                st.info("Columnas disponibles: " + ", ".join(df.columns))
                return None
            
            # Crear columnas opcionales si no existen
            optional_cols = {
                'Almacén': 'Almacén General',
                'Código de artículo': 'N/A',
                'Nombre del producto': 'Producto sin nombre'
            }
            
            for col, default_val in optional_cols.items():
                if col not in df.columns:
                    df[col] = default_val
                    st.info(f"Columna '{col}' creada con valor por defecto: '{default_val}'")
            
            # Procesar y limpiar datos
            df['Inventario físico'] = pd.to_numeric(df['Inventario físico'], errors='coerce').fillna(0).astype(int)
            df['Id de pallet'] = df['Id de pallet'].astype(str).str.strip()
            
            # Estadísticas del archivo
            total_records = len(df)
            duplicates = df['Id de pallet'].duplicated().sum()
            zero_inventory = (df['Inventario físico'] == 0).sum()
            
            # Mostrar resumen de carga
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Registros Cargados", total_records)
            with col2:
                st.metric("Duplicados Detectados", duplicates)
            with col3:
                st.metric("Con Inventario Cero", zero_inventory)
            
            if duplicates > 0:
                st.warning(f"⚠️ Se detectaron {duplicates} IDs duplicados. Considera limpiar el archivo.")
            
            return df
            
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        st.error("Verifica que el archivo sea un Excel válido (.xlsx) y contenga las columnas requeridas.")
        return None

def buscar_info_pallet_optimized(id_pallet, df_inventario):
    """Versión optimizada de búsqueda de información del pallet"""
    if df_inventario is None or not id_pallet:
        return None, None, None, None, False
    
    # Normalizar ID para búsqueda
    id_pallet_clean = str(id_pallet).strip().upper()
    
    # Crear máscara de búsqueda más robusta
    mask = df_inventario['Id de pallet'].astype(str).str.strip().str.upper() == id_pallet_clean
    matches = df_inventario[mask]
    
    if not matches.empty:
        match = matches.iloc[0]  # Tomar el primer match
        
        almacen = str(match.get('Almacén', 'N/A')).strip()
        codigo = str(match.get('Código de artículo', 'N/A')).strip()
        nombre = str(match.get('Nombre del producto', 'N/A')).strip()
        
        try:
            inv_sistema = int(float(match.get('Inventario físico', 0)))
        except (ValueError, TypeError):
            inv_sistema = 0
        
        return almacen, codigo, nombre, inv_sistema, True
    
    return None, None, None, None, False

def calcular_estadisticas_avanzadas():
    """Calcula estadísticas avanzadas del conteo"""
    if not st.session_state.conteo_fisico:
        return {
            'total': 0, 'exactos': 0, 'sobrantes': 0, 'faltantes': 0, 
            'no_encontrados': 0, 'precision': 0, 'efficiency': 0,
            'total_variance': 0, 'avg_difference': 0
        }
    
    df = pd.DataFrame(st.session_state.conteo_fisico)
    
    total = len(df)
    exactos = len(df[df['diferencia'] == 0])
    sobrantes = len(df[df['diferencia'] > 0])
    faltantes = len(df[df['diferencia'] < 0])
    no_encontrados = len(df[df['inv_sistema'].isna()])
    
    # Métricas avanzadas
    precision = (exactos / total * 100) if total > 0 else 0
    efficiency = (total / (total + no_encontrados) * 100) if (total + no_encontrados) > 0 else 100
    total_variance = df['diferencia'].var() if len(df) > 1 else 0
    avg_difference = df['diferencia'].mean() if len(df) > 0 else 0
    
    return {
        'total': total, 'exactos': exactos, 'sobrantes': sobrantes, 
        'faltantes': faltantes, 'no_encontrados': no_encontrados,
        'precision': precision, 'efficiency': efficiency,
        'total_variance': total_variance, 'avg_difference': avg_difference
    }

def procesar_pallet_optimized(numero_tablilla, id_pallet, cantidad_contada):
    """Procesamiento optimizado de pallets con mejor feedback"""
    start_time = datetime.now()
    
    # Buscar información
    almacen, codigo, nombre, inv_sistema, found = buscar_info_pallet_optimized(
        id_pallet, st.session_state.inventario_sistema
    )
    
    # Calcular diferencia
    diferencia = cantidad_contada - (inv_sistema if inv_sistema is not None else 0)
    
    # Crear registro optimizado
    nuevo_item = {
        'numero_tablilla': numero_tablilla,
        'id_pallet': str(id_pallet).strip(),
        'codigo_articulo': codigo if codigo != 'N/A' else '',
        'nombre_producto': nombre if nombre != 'N/A' else '',
        'almacen': almacen if almacen != 'N/A' else '',
        'cantidad_contada': int(cantidad_contada),
        'inv_sistema': inv_sistema,
        'diferencia': diferencia,
        'timestamp': datetime.now(),
        'found_in_system': found,
        'processing_time': (datetime.now() - start_time).total_seconds()
    }
    
    # Agregar al conteo
    st.session_state.conteo_fisico.append(nuevo_item)
    st.session_state.last_added_id = id_pallet
    
    # Actualizar estadísticas de sesión
    st.session_state.session_stats['total_processed'] += 1
    
    # Feedback visual mejorado
    if found:
        if diferencia == 0:
            st.success(f"✅ {id_pallet}: Cantidad exacta ({cantidad_contada})")
        elif diferencia > 0:
            st.warning(f"🔼 {id_pallet}: Sobrante de {diferencia} unidades")
        else:
            st.error(f"🔽 {id_pallet}: Faltante de {abs(diferencia)} unidades")
    else:
        st.info(f"❓ {id_pallet}: No encontrado en sistema - {cantidad_contada} unidades")
    
    return True

# Dashboard ejecutivo avanzado
def create_executive_dashboard():
    """Crea dashboard ejecutivo con visualizaciones avanzadas"""
    stats = calcular_estadisticas_avanzadas()
    
    if stats['total'] == 0:
        st.info("No hay datos para mostrar en el dashboard")
        return
    
    st.markdown('<div class="executive-dashboard">', unsafe_allow_html=True)
    st.subheader("🎯 Dashboard Ejecutivo")
    
    # KPIs principales con gauge charts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Gauge de precisión
        fig_precision = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = stats['precision'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Precisión de Inventario (%)"},
            delta = {'reference': 95, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 70], 'color': "lightgray"},
                    {'range': [70, 90], 'color': "yellow"},
                    {'range': [90, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        fig_precision.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_precision, use_container_width=True)
    
    with col2:
        # Gauge de eficiencia
        fig_efficiency = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = stats['efficiency'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Eficiencia de Conteo (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 80], 'color': "lightgray"},
                    {'range': [80, 95], 'color': "yellow"},
                    {'range': [95, 100], 'color': "lightgreen"}
                ]
            }
        ))
        fig_efficiency.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_efficiency, use_container_width=True)
    
    with col3:
        # Distribución en sunburst
        df = pd.DataFrame(st.session_state.conteo_fisico)
        
        if not df.empty and 'almacen' in df.columns:
            # Crear datos para sunburst
            sunburst_data = []
            
            # Nivel 1: Por almacén
            almacen_stats = df.groupby('almacen').agg({
                'diferencia': lambda x: 'Exacto' if (x == 0).all() else 'Con diferencias'
            }).reset_index()
            
            for _, row in almacen_stats.iterrows():
                almacen_df = df[df['almacen'] == row['almacen']]
                exactos_alm = len(almacen_df[almacen_df['diferencia'] == 0])
                diferencias_alm = len(almacen_df[almacen_df['diferencia'] != 0])
                
                sunburst_data.extend([
                    dict(ids=f"{row['almacen']}-Exactos", labels="Exactos", parents=row['almacen'], values=exactos_alm),
                    dict(ids=f"{row['almacen']}-Diferencias", labels="Diferencias", parents=row['almacen'], values=diferencias_alm),
                ])
            
            # Agregar padres (almacenes)
            for almacen in df['almacen'].unique():
                total_almacen = len(df[df['almacen'] == almacen])
                sunburst_data.append(dict(ids=almacen, labels=almacen, parents="", values=total_almacen))
            
            if sunburst_data:
                fig_sunburst = go.Figure(go.Sunburst(
                    ids=[d['ids'] for d in sunburst_data],
                    labels=[d['labels'] for d in sunburst_data],
                    parents=[d['parents'] for d in sunburst_data],
                    values=[d['values'] for d in sunburst_data],
                    branchvalues="total",
                ))
                fig_sunburst.update_layout(
                    title="Distribución por Almacén",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_sunburst, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def generar_reporte_excel():
    """Genera reporte Excel mejorado con análisis ejecutivo - Optimizado para Streamlit Cloud"""
    if not st.session_state.conteo_fisico:
        return None
    
    try:
        df_conteo = pd.DataFrame(st.session_state.conteo_fisico)
        
        # Crear buffer de memoria optimizado
        output = io.BytesIO()
        
        # Usar openpyxl en lugar de xlsxwriter para mejor compatibilidad con Streamlit Cloud
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de resumen ejecutivo
            stats = calcular_estadisticas_avanzadas()
            
            resumen_data = {
                'KPI': [
                    'Fecha del Análisis', 'Hora de Inicio', 'Duración de Sesión (min)',
                    'Total Pallets Procesados', 'Pallets con Cantidad Exacta',
                    'Pallets con Sobrantes', 'Pallets con Faltantes',
                    'Pallets NO Encontrados', 'Precisión del Inventario (%)',
                    'Eficiencia de Conteo (%)', 'Varianza Total', 'Diferencia Promedio'
                ],
                'Valor': [
                    datetime.now().strftime("%Y-%m-%d"),
                    st.session_state.session_stats['start_time'].strftime("%H:%M:%S"),
                    round((datetime.now() - st.session_state.session_stats['start_time']).total_seconds() / 60, 1),
                    stats['total'], stats['exactos'], stats['sobrantes'],
                    stats['faltantes'], stats['no_encontrados'],
                    round(stats['precision'], 2), round(stats['efficiency'], 2),
                    round(stats['total_variance'], 2), round(stats['avg_difference'], 2)
                ]
            }
            
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
            
            # Hoja de datos completos
            df_conteo_clean = df_conteo.copy()
            # Limpiar datos para Excel
            for col in df_conteo_clean.columns:
                if df_conteo_clean[col].dtype == 'object':
                    df_conteo_clean[col] = df_conteo_clean[col].astype(str)
            
            df_conteo_clean.to_excel(writer, sheet_name='Datos Completos', index=False)
            
            # Hoja de diferencias (solo registros con diferencias)
            df_diferencias = df_conteo[df_conteo['diferencia'] != 0].copy()
            if not df_diferencias.empty:
                for col in df_diferencias.columns:
                    if df_diferencias[col].dtype == 'object':
                        df_diferencias[col] = df_diferencias[col].astype(str)
                df_diferencias.to_excel(writer, sheet_name='Discrepancias', index=False)
        
        # Asegurar que el buffer esté al inicio
        output.seek(0)
        return output.getvalue()  # Retornar bytes en lugar del objeto BytesIO
        
    except Exception as e:
        st.error(f"Error generando reporte Excel: {str(e)}")
        # Fallback: generar CSV simple
        df_conteo = pd.DataFrame(st.session_state.conteo_fisico)
        csv_output = df_conteo.to_csv(index=False)
        return csv_output.encode('utf-8')

# Función principal mejorada
def main():
    """Función principal de la aplicación mejorada"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>📦 Visor de Inventario Pro - Enhanced Edition</h1>
        <p>Sistema avanzado con navegación optimizada y analytics ejecutivos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar mejorado
    with st.sidebar:
        st.header("📁 Gestión de Inventario")
        
        # Información de sesión
        if st.session_state.session_stats['total_processed'] > 0:
            session_time = (datetime.now() - st.session_state.session_stats['start_time']).total_seconds() / 60
            st.metric("Tiempo de Sesión", f"{session_time:.1f} min")
            st.metric("Pallets Procesados", st.session_state.session_stats['total_processed'])
            
            if session_time > 0:
                rate = st.session_state.session_stats['total_processed'] / session_time
                st.metric("Velocidad", f"{rate:.1f} pallets/min")
        
        st.divider()
        
        # Carga de archivo
        uploaded_file = st.file_uploader(
            "Selecciona archivo Excel de inventario",
            type=['xlsx'],
            help="Debe contener: 'Id de pallet' e 'Inventario físico'"
        )
        
        if uploaded_file and not st.session_state.archivo_cargado:
            inventario_df = cargar_inventario(uploaded_file)
            if inventario_df is not None:
                st.session_state.inventario_sistema = inventario_df
                st.session_state.archivo_cargado = True
                st.success(f"✅ Inventario cargado: {len(inventario_df):,} registros")
                st.rerun()
        
        if st.session_state.archivo_cargado:
            st.success(f"📊 Inventario activo: {len(st.session_state.inventario_sistema):,} pallets")
            
            if st.button("🔄 Cargar nuevo archivo"):
                # Reset completo del estado
                for key in ['inventario_sistema', 'conteo_fisico', 'archivo_cargado', 'last_added_id']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    # Contenido principal
    if not st.session_state.archivo_cargado:
        st.info("👆 Para comenzar, carga un archivo de inventario en el panel lateral")
        
        # Ejemplo mejorado
        st.subheader("📋 Estructura de archivo requerida")
        ejemplo_data = {
            'Id de pallet': ['PLT001', 'PLT002', 'PLT003', 'PLT004'],
            'Inventario físico': [50, 25, 100, 0],
            'Almacén': ['A-001', 'B-002', 'A-001', 'C-003'],
            'Código de artículo': ['ART001', 'ART002', 'ART003', 'ART004'],
            'Nombre del producto': ['Producto A', 'Producto B', 'Producto C', 'Producto D']
        }
        st.dataframe(pd.DataFrame(ejemplo_data), use_container_width=True)
        
        st.info("💡 Las columnas 'Almacén', 'Código de artículo' y 'Nombre del producto' son opcionales")
        
    else:
        # Dashboard de estadísticas
        stats = calcular_estadisticas_avanzadas()
        
        # Métricas principales
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total", stats['total'], help="Pallets procesados")
        with col2:
            st.metric("Exactos", stats['exactos'], 
                     delta=f"{stats['precision']:.1f}%", 
                     help="Cantidades que coinciden exactamente")
        with col3:
            st.metric("Sobrantes", stats['sobrantes'], 
                     delta="+" if stats['sobrantes'] > 0 else None,
                     help="Cantidad física mayor al sistema")
        with col4:
            st.metric("Faltantes", stats['faltantes'],
                     delta="-" if stats['faltantes'] > 0 else None,
                     help="Cantidad física menor al sistema")
        with col5:
            st.metric("No Encontrados", stats['no_encontrados'],
                     help="Pallets no registrados en el sistema")
        
        # Dashboard ejecutivo
        if stats['total'] > 0:
            create_executive_dashboard()
        
        # Sección de digitación mejorada
        st.subheader("⌨️ Digitación Rápida")
        
        # Instrucciones mejoradas
        st.markdown("""
        <div class="keyboard-instructions">
            <i class="fas fa-info-circle"></i>
            <strong>🚀 Navegación rápida:</strong> Tablilla → Enter → ID Pallet → Enter → Cantidad → Enter (agregar automáticamente)
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="input-section active">', unsafe_allow_html=True)
            
            # Usar contador para keys dinámicas
            counter = st.session_state.campo_counter
            
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
            
            with col1:
                numero_tablilla = st.text_input(
                    "📋 Tablilla",
                    placeholder="001",
                    key=f"tablilla_{counter}",
                    help="Presiona Enter para ir al siguiente campo"
                )
            
            with col2:
                id_pallet = st.text_input(
                    "🏷️ ID Pallet",
                    placeholder="PLT001",
                    key=f"pallet_{counter}",
                    help="El sistema detectará la información automáticamente"
                )
            
            with col3:
                cantidad_contada = st.number_input(
                    "📊 Cantidad",
                    min_value=0,
                    step=1,
                    key=f"cantidad_{counter}",
                    help="Presiona Enter aquí para agregar automáticamente"
                )
            
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)  # Espaciado
                agregar_btn = st.button(
                    "➕ Agregar", 
                    use_container_width=True,
                    type="primary",
                    key=f"btn_agregar_{counter}"
                )
            
            # Detección en tiempo real
            if id_pallet:
                almacen, codigo, nombre, inv_sistema, found = buscar_info_pallet_optimized(
                    id_pallet, st.session_state.inventario_sistema
                )
                
                if found:
                    st.success(f"✅ **{almacen}** | {codigo} | {nombre[:40]}{'...' if len(nombre) > 40 else ''} | Sistema: **{inv_sistema}**")
                else:
                    st.warning("⚠️ Pallet no encontrado en el sistema")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Procesar cuando se presiona el botón
            if agregar_btn and numero_tablilla and id_pallet is not None:
                if procesar_pallet_optimized(numero_tablilla, id_pallet, cantidad_contada):
                    # Incrementar contador para limpiar campos
                    st.session_state.campo_counter += 1
                    st.rerun()
            elif agregar_btn:
                st.error("Por favor completa Tablilla e ID de Pallet")
        
        # Mostrar resultados si existen
        if st.session_state.conteo_fisico:
            st.subheader("📋 Resultados del Conteo")
            
            df_display = pd.DataFrame(st.session_state.conteo_fisico)
            
            # Controles de filtro
            col_search, col_filter = st.columns([2, 1])
            
            with col_search:
                search_term = st.text_input("🔍 Buscar", placeholder="ID, código, producto, almacén...")
            
            with col_filter:
                filter_option = st.selectbox(
                    "Filtrar por estado",
                    ["Todos", "Exactos", "Sobrantes", "Faltantes", "No encontrados"]
                )
            
            # Aplicar filtros
            df_filtered = df_display.copy()
            
            if search_term:
                mask = df_filtered.astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                df_filtered = df_filtered[mask]
            
            if filter_option != "Todos":
                if filter_option == "Exactos":
                    df_filtered = df_filtered[df_filtered['diferencia'] == 0]
                elif filter_option == "Sobrantes":
                    df_filtered = df_filtered[df_filtered['diferencia'] > 0]
                elif filter_option == "Faltantes":
                    df_filtered = df_filtered[df_filtered['diferencia'] < 0]
                elif filter_option == "No encontrados":
                    df_filtered = df_filtered[df_filtered['inv_sistema'].isna()]
            
            # Formatear para mostrar
            if not df_filtered.empty:
                display_df = df_filtered.copy()
                
                # Formatear diferencias con íconos
                def format_diff(val):
                    if pd.isna(val):
                        return "❓ N/A"
                    elif val > 0:
                        return f"🔼 +{val}"
                    elif val < 0:
                        return f"🔽 {val}"
                    else:
                        return f"✅ {val}"
                
                display_df['Estado'] = display_df['diferencia'].apply(format_diff)
                
                # Mostrar tabla
                st.dataframe(
                    display_df[['numero_tablilla', 'id_pallet', 'almacen', 'codigo_articulo', 
                               'nombre_producto', 'cantidad_contada', 'inv_sistema', 'Estado']],
                    use_container_width=True,
                    column_config={
                        'numero_tablilla': 'Tablilla',
                        'id_pallet': 'ID Pallet',
                        'almacen': 'Almacén',
                        'codigo_articulo': 'Código',
                        'nombre_producto': 'Producto',
                        'cantidad_contada': 'Contado',
                        'inv_sistema': 'Sistema',
                        'Estado': 'Estado'
                    }
                )
                
                # Botones de acción
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🗑️ Limpiar Todo", use_container_width=True):
                        st.session_state.conteo_fisico = []
                        st.session_state.campo_counter += 1
                        st.rerun()
                
                with col2:
                    # Generar reporte Excel optimizado para Streamlit Cloud
                    if st.button("📊 Generar Excel", use_container_width=True):
                        try:
                            with st.spinner("Generando reporte..."):
                                excel_data = generar_reporte_excel()
                                if excel_data:
                                    # Determinar tipo de archivo basado en el contenido
                                    if isinstance(excel_data, bytes) and excel_data.startswith(b'PK'):
                                        # Es un archivo Excel válido
                                        file_name = f"Inventario_Pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    else:
                                        # Es CSV (fallback)
                                        file_name = f"Inventario_Pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                                        mime_type = "text/csv"
                                    
                                    st.download_button(
                                        label=f"⬇️ Descargar {file_name.split('.')[-1].upper()}",
                                        data=excel_data,
                                        file_name=file_name,
                                        mime=mime_type,
                                        use_container_width=True,
                                        key=f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                    )
                                    st.success("¡Reporte generado exitosamente!")
                                else:
                                    st.error("No hay datos para generar el reporte")
                        except Exception as e:
                            st.error(f"Error generando reporte: {str(e)}")
                            # Ofrecer descarga CSV como alternativa
                            df_conteo = pd.DataFrame(st.session_state.conteo_fisico)
                            csv_data = df_conteo.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="⬇️ Descargar CSV (Alternativo)",
                                data=csv_data,
                                file_name=f"Inventario_Pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                
                with col3:
                    if st.button("📈 Actualizar Dashboard", use_container_width=True):
                        st.rerun()
            
            else:
                st.info("No se encontraron resultados con los filtros aplicados")

# Ejecutar aplicación
if __name__ == "__main__":
    main()

# Footer mejorado
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <h4>📦 Visor de Inventario Pro - Enhanced Edition</h4>
    <p>Sistema avanzado con navegación optimizada por teclado y análisis ejecutivo</p>
    <p><em>Versión final optimizada para Streamlit Cloud</em></p>
</div>
""", unsafe_allow_html=True)