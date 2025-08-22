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

# CSS personalizado mejorado
st.markdown("""
<style>
    /* Estilos principales */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .input-section {
        background: rgba(0, 123, 255, 0.05);
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        transition: all 0.3s ease;
    }
    
    .pallet-info-detected {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #155724;
        font-weight: bold;
        animation: pulse-success 2s infinite;
    }
    
    .pallet-not-found {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #721c24;
        font-weight: bold;
    }
    
    .duplicate-modal {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    }
    
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
    
    @keyframes pulse-success {
        0%, 100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
        50% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease;
    }
    
    .executive-dashboard {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
</style>

<script>
// Sistema de navegación por teclado simplificado para campos separados
function initKeyboardNavigation() {
    setTimeout(() => {
        const inputs = document.querySelectorAll('input[type="text"], input[type="number"]');
        const visibleInputs = Array.from(inputs).filter(input => {
            const rect = input.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        });
        
                 if (visibleInputs.length >= 3) {
             // Configurar navegación entre los primeros 3 campos
             visibleInputs[0].addEventListener('keydown', (e) => {
                 if (e.key === 'Enter') {
                     e.preventDefault();
                     visibleInputs[1].focus();
                     visibleInputs[1].select();
                 }
             });
             
             visibleInputs[1].addEventListener('keydown', (e) => {
                 if (e.key === 'Enter') {
                     e.preventDefault();
                     visibleInputs[2].focus();
                     visibleInputs[2].select();
                 }
             });
             
             // En el último campo (cantidad), Enter activa el botón agregar
             visibleInputs[2].addEventListener('keydown', (e) => {
                 if (e.key === 'Enter') {
                     e.preventDefault();
                     // Buscar el botón "Agregar al Conteo"
                     const addButton = document.querySelector('button[kind="primary"]');
                     if (addButton && addButton.textContent.includes('Agregar')) {
                         console.log('✅ Enter en cantidad - activando botón agregar');
                         addButton.click();
                     } else {
                         // Buscar por otros selectores
                         const buttons = document.querySelectorAll('button');
                         for (const button of buttons) {
                             if (button.textContent.includes('Agregar') || button.textContent.includes('➕')) {
                                 console.log('✅ Botón agregar encontrado - haciendo clic');
                                 button.click();
                                 break;
                             }
                         }
                     }
                 }
             });
             
             console.log('✅ Navegación configurada para', visibleInputs.length, 'campos (Enter en cantidad agrega automáticamente)');
         }
    }, 500);
}

// Inicializar cuando Streamlit termine de cargar
document.addEventListener('DOMContentLoaded', initKeyboardNavigation);
window.addEventListener('load', initKeyboardNavigation);

// Reinicializar después de cambios en Streamlit
const observer = new MutationObserver(() => {
    setTimeout(initKeyboardNavigation, 200);
});
observer.observe(document.body, { childList: true, subtree: true });

// Función para auto-focus en primer campo después de agregar
function autoFocusFirstField() {
    setTimeout(() => {
        const inputs = document.querySelectorAll('input[type="text"], input[type="number"]');
        const visibleInputs = Array.from(inputs).filter(input => {
            const rect = input.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        });
        
        if (visibleInputs.length > 0) {
            visibleInputs[0].focus();
            visibleInputs[0].select();
            console.log('🎯 Auto-focus en primer campo activado');
        }
    }, 300);
}

// Detectar cuando se agrega un registro y hacer auto-focus
const statusObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && node.querySelector) {
                    // Buscar mensajes de éxito que indican que se agregó un registro
                    const successMessages = node.querySelectorAll('.stAlert, .stSuccess, [data-testid="stAlert"]');
                    if (successMessages.length > 0) {
                        autoFocusFirstField();
                    }
                }
            });
        }
    });
});
statusObserver.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Inicializar estado de la sesión
def init_session_state():
    """Inicializar estado de sesión"""
    defaults = {
        'inventario_sistema': None,
        'conteo_fisico': [],
        'archivo_cargado': False,
        'campo_counter': 0,
        'mostrar_duplicado': False,
        'pallet_duplicado': None,
        'temp_data': None,
        'editando': False,
        'registro_seleccionado': None,
        'session_stats': {
            'start_time': datetime.now(),
            'total_processed': 0,
        }
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# Funciones auxiliares
def cargar_inventario(archivo):
    """Carga y valida el archivo de inventario"""
    try:
        with st.spinner("Cargando y validando archivo..."):
            df = pd.read_excel(archivo, dtype=str, engine='openpyxl')
            df = df.dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            
            required_cols = ['Id de pallet', 'Inventario físico']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Columnas requeridas faltantes: {', '.join(missing_cols)}")
                st.info("Columnas disponibles: " + ", ".join(df.columns))
                return None
            
            optional_cols = {
                'Almacén': 'Almacén General',
                'Código de artículo': 'N/A',
                'Nombre del producto': 'Producto sin nombre'
            }
            
            for col, default_val in optional_cols.items():
                if col not in df.columns:
                    df[col] = default_val
                    st.info(f"Columna '{col}' creada con valor por defecto: '{default_val}'")
            
            df['Inventario físico'] = pd.to_numeric(df['Inventario físico'], errors='coerce').fillna(0).astype(int)
            df['Id de pallet'] = df['Id de pallet'].astype(str).str.strip()
            
            total_records = len(df)
            duplicates = df['Id de pallet'].duplicated().sum()
            zero_inventory = (df['Inventario físico'] == 0).sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Registros Cargados", total_records)
            with col2:
                st.metric("Duplicados Detectados", duplicates)
            with col3:
                st.metric("Con Inventario Cero", zero_inventory)
            
            if duplicates > 0:
                st.warning(f"⚠️ Se detectaron {duplicates} IDs duplicados.")
            
            return df
            
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None

def buscar_info_pallet(id_pallet, df_inventario):
    """Busca información del pallet en el inventario del sistema"""
    if df_inventario is None or id_pallet == "":
        return None, None, None, None
    
    mask = df_inventario['Id de pallet'].astype(str).str.strip() == str(id_pallet).strip()
    match = df_inventario[mask]
    
    if not match.empty:
        almacen = str(match.iloc[0].get('Almacén', 'N/A')).strip()
        inv_sistema = match.iloc[0].get('Inventario físico', 0)
        codigo = str(match.iloc[0].get('Código de artículo', 'N/A')).strip()
        nombre = str(match.iloc[0].get('Nombre del producto', 'N/A')).strip()
        
        try:
            inv_sistema = int(inv_sistema) if inv_sistema is not None else 0
        except:
            inv_sistema = 0
            
        return almacen, codigo, nombre, inv_sistema
    else:
        return None, None, None, None

def calcular_estadisticas():
    """Calcula estadísticas del conteo"""
    if not st.session_state.conteo_fisico:
        return 0, 0, 0, 0, 0
    
    total = len(st.session_state.conteo_fisico)
    exactos = len([item for item in st.session_state.conteo_fisico if item['diferencia'] == 0])
    sobrantes = len([item for item in st.session_state.conteo_fisico if item['diferencia'] > 0])
    faltantes = len([item for item in st.session_state.conteo_fisico if item['diferencia'] < 0])
    no_encontrados = len([item for item in st.session_state.conteo_fisico if item['inv_sistema'] is None])
    
    return total, exactos, sobrantes, faltantes, no_encontrados

def procesar_pallet(numero_tablilla, id_pallet, cantidad_contada):
    """Función para procesar y agregar un pallet al conteo"""
    # Buscar información del pallet
    almacen, codigo, nombre, inv_sistema = buscar_info_pallet(id_pallet, st.session_state.inventario_sistema)
    
    # Calcular diferencia
    diferencia = cantidad_contada - (inv_sistema if inv_sistema is not None else 0)
    
    # Crear nuevo item
    nuevo_item = {
        'numero_tablilla': numero_tablilla,
        'id_pallet': id_pallet,
        'codigo_articulo': codigo if codigo != 'N/A' else '',
        'nombre_producto': nombre if nombre != 'N/A' else '',
        'almacen': almacen if almacen != 'N/A' else '',
        'cantidad_contada': cantidad_contada,
        'inv_sistema': inv_sistema,
        'diferencia': diferencia,
        'timestamp': datetime.now()
    }
    
    # Agregar al conteo
    st.session_state.conteo_fisico.append(nuevo_item)
    
    # Feedback visual
    if inv_sistema is not None:
        if diferencia == 0:
            st.success(f"✅ {id_pallet}: Cantidad exacta ({cantidad_contada}) - {nombre[:30]}")
        elif diferencia > 0:
            st.warning(f"🔼 {id_pallet}: Sobrante de {diferencia} unidades - {nombre[:30]}")
        else:
            st.error(f"🔽 {id_pallet}: Faltante de {abs(diferencia)} unidades - {nombre[:30]}")
    else:
        st.info(f"❓ {id_pallet}: No encontrado en sistema - {cantidad_contada} unidades")

def limpiar_campos():
    """Función para limpiar los campos de entrada usando keys dinámicas"""
    if 'campo_counter' not in st.session_state:
        st.session_state.campo_counter = 0
    st.session_state.campo_counter += 1

def generar_reporte_excel():
    """Genera reporte profesional en formato Excel"""
    if not st.session_state.conteo_fisico:
        return None
    
    try:
        df_conteo = pd.DataFrame(st.session_state.conteo_fisico)
        
        # Merge con inventario del sistema
        df_sistema = st.session_state.inventario_sistema.copy()
        df_sistema['Id de pallet'] = df_sistema['Id de pallet'].astype(str).str.strip()
        df_conteo['id_pallet'] = df_conteo['id_pallet'].astype(str).str.strip()
        
        # LEFT JOIN desde conteo
        df_completo = pd.merge(df_conteo, df_sistema, left_on='id_pallet', right_on='Id de pallet', 
                              how='left', indicator=True, suffixes=('_conteo', '_sistema'))
        
        # Separar en categorías
        no_encontrados = df_completo[df_completo['_merge'] == 'left_only'].copy()
        encontrados = df_completo[df_completo['_merge'] == 'both'].copy()
        
        if not encontrados.empty:
            encontrados['diferencia_calc'] = encontrados['cantidad_contada'] - encontrados['inv_sistema']
            diferencias = encontrados[encontrados['diferencia_calc'] != 0].copy()
            exactos = encontrados[encontrados['diferencia_calc'] == 0].copy()
        else:
            diferencias = pd.DataFrame()
            exactos = pd.DataFrame()
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de resumen ejecutivo
            total, exactos_count, sobrantes, faltantes, no_encontrados_count = calcular_estadisticas()
            
            resumen_data = {
                'Métrica': [
                    'Fecha del Reporte',
                    'Total Pallets Digitados',
                    'Pallets Encontrados en Sistema',
                    'Pallets con Cantidad Exacta',
                    'Pallets con Diferencias',
                    'Pallets NO Encontrados en Sistema',
                    'Precisión del Inventario (%)',
                    'Total Sobrantes',
                    'Total Faltantes'
                ],
                'Valor': [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    len(df_conteo),
                    len(encontrados),
                    len(exactos),
                    len(diferencias),
                    len(no_encontrados),
                    round((len(exactos) / len(encontrados) * 100) if len(encontrados) > 0 else 0, 2),
                    sobrantes,
                    faltantes
                ]
            }
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
            
            # Hoja de discrepancias
            if not diferencias.empty:
                cols_diferencias = ['numero_tablilla', 'id_pallet', 'almacen', 'codigo_articulo', 
                                   'nombre_producto', 'cantidad_contada', 'inv_sistema', 'diferencia_calc']
                diferencias_export = diferencias[cols_diferencias].copy()
                diferencias_export.columns = ['Tablilla', 'ID Pallet', 'Almacén', 'Código', 
                                             'Producto', 'Contado', 'Sistema', 'Diferencia']
                diferencias_export.to_excel(writer, sheet_name='Discrepancias', index=False)
            
            # Hoja de exactos
            if not exactos.empty:
                cols_exactos = ['numero_tablilla', 'id_pallet', 'almacen', 'codigo_articulo', 
                               'nombre_producto', 'cantidad_contada']
                exactos_export = exactos[cols_exactos].copy()
                exactos_export.columns = ['Tablilla', 'ID Pallet', 'Almacén', 'Código', 'Producto', 'Cantidad']
                exactos_export.to_excel(writer, sheet_name='Cantidades Exactas', index=False)
            
            # Hoja de no encontrados
            if not no_encontrados.empty:
                cols_no_encontrados = ['numero_tablilla', 'id_pallet', 'almacen', 'cantidad_contada']
                no_encontrados_export = no_encontrados[cols_no_encontrados].copy()
                no_encontrados_export.columns = ['Tablilla', 'ID Pallet', 'Almacén', 'Cantidad']
                no_encontrados_export.to_excel(writer, sheet_name='No Encontrados', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        st.error(f"Error generando reporte: {str(e)}")
        return None

# Dashboard ejecutivo
def create_executive_dashboard():
    """Crea dashboard ejecutivo con visualizaciones avanzadas"""
    total, exactos, sobrantes, faltantes, no_encontrados = calcular_estadisticas()
    
    if total == 0:
        return
    
    st.markdown('<div class="executive-dashboard">', unsafe_allow_html=True)
    st.subheader("🎯 Dashboard Ejecutivo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Gráfico de dona
        labels = ['Exactos', 'Sobrantes', 'Faltantes', 'No Encontrados']
        values = [exactos, sobrantes, faltantes, no_encontrados]
        colors = ['#27ae60', '#f39c12', '#e74c3c', '#9b59b6']
        
        fig_dona = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.4,
            marker_colors=colors,
            textinfo='label+percent+value'
        )])
        fig_dona.update_layout(title="Distribución de Resultados", height=300)
        st.plotly_chart(fig_dona, use_container_width=True)
    
    with col2:
        # Gauge de precisión
        precision = (exactos / total * 100) if total > 0 else 0
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = precision,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Precisión del Inventario (%)"},
            delta = {'reference': 95},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 70], 'color': "lightgray"},
                    {'range': [70, 90], 'color': "yellow"},
                    {'range': [90, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col3:
        # Análisis por almacén
        if st.session_state.conteo_fisico:
            df = pd.DataFrame(st.session_state.conteo_fisico)
            if 'almacen' in df.columns:
                almacen_counts = df['almacen'].value_counts()
                
                fig_bar = px.bar(
                    x=almacen_counts.values,
                    y=almacen_counts.index,
                    orientation='h',
                    title="Pallets por Almacén",
                    labels={'x': 'Cantidad', 'y': 'Almacén'},
                    color=almacen_counts.values,
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Función principal
def main():
    """Función principal de la aplicación"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>📦 Visor de Inventario Pro v2.0</h1>
        <p>Sistema avanzado de análisis de inventarios físicos</p>
        <p><small>⌨️ Navegación: Tablilla → Enter → ID Pallet → Enter → Cantidad → Enter (agregar automáticamente)</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para carga de archivo
    with st.sidebar:
        st.header("📁 Cargar Inventario")
        
        uploaded_file = st.file_uploader(
            "Selecciona el archivo Excel de inventario",
            type=['xlsx'],
            help="El archivo debe contener las columnas: 'Id de pallet' e 'Inventario físico'"
        )
        
        if uploaded_file is not None and not st.session_state.archivo_cargado:
            inventario_df = cargar_inventario(uploaded_file)
            if inventario_df is not None:
                st.session_state.inventario_sistema = inventario_df
                st.session_state.archivo_cargado = True
                st.success(f"✅ Inventario cargado: {len(inventario_df)} registros")
                st.rerun()
        
        if st.session_state.archivo_cargado:
            st.success(f"📊 Inventario activo: {len(st.session_state.inventario_sistema)} pallets")
            
            if st.button("🔄 Cargar nuevo archivo"):
                st.session_state.inventario_sistema = None
                st.session_state.archivo_cargado = False
                st.session_state.conteo_fisico = []
                st.rerun()
        
        # Información de sesión
        if st.session_state.session_stats['total_processed'] > 0:
            st.divider()
            session_time = (datetime.now() - st.session_state.session_stats['start_time']).total_seconds() / 60
            st.metric("Tiempo de Sesión", f"{session_time:.1f} min")
            st.metric("Pallets Procesados", st.session_state.session_stats['total_processed'])

    # Contenido principal
    if not st.session_state.archivo_cargado:
        st.info("👆 Para comenzar, carga un archivo de inventario en el panel lateral")
        
        st.subheader("📋 Estructura de archivo esperada")
        ejemplo_data = {
            'Id de pallet': ['PLT001', 'PLT002', 'PLT003'],
            'Inventario físico': [50, 25, 100],
            'Almacén': ['A-001', 'B-002', 'A-001'],
            'Código de artículo': ['ART001', 'ART002', 'ART003'],
            'Nombre del producto': ['Producto Ejemplo 1', 'Producto Ejemplo 2', 'Producto Ejemplo 3']
        }
        st.dataframe(pd.DataFrame(ejemplo_data), use_container_width=True)
        
    else:
        # Dashboard de estadísticas
        st.subheader("📊 Estadísticas en Tiempo Real")
        total, exactos, sobrantes, faltantes, no_encontrados = calcular_estadisticas()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Pallets", total, help="Pallets digitados hasta ahora")
        with col2:
            st.metric("Exactos", exactos, help="Cantidad coincide exactamente")
        with col3:
            st.metric("Sobrantes", sobrantes, help="Cantidad contada mayor al sistema")
        with col4:
            st.metric("Faltantes", faltantes, help="Cantidad contada menor al sistema")
        with col5:
            st.metric("No Encontrados", no_encontrados, help="Pallets no están en el sistema")
        
        # Dashboard ejecutivo
        if total > 0:
            create_executive_dashboard()
        
        # Digitación con campos separados
        st.subheader("⌨️ Digitación de Conteo Físico")
        
                         # Instrucciones
        st.markdown("""
        <div class="keyboard-instructions">
            <i class="fas fa-keyboard"></i>
            <strong>🚀 Navegación Optimizada:</strong><br>
            1️⃣ <strong>Tablilla</strong> → <kbd>Enter</kbd> → 2️⃣ <strong>ID Pallet</strong> → <kbd>Enter</kbd> → 3️⃣ <strong>Cantidad</strong> → <kbd>Enter</kbd> (agregar automáticamente)<br>
            <small>💡 La información del pallet aparece automáticamente al escribir el ID | También puedes usar Tab</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Inicializar contador para keys dinámicas
        if 'campo_counter' not in st.session_state:
            st.session_state.campo_counter = 0
        
        # Usar columnas para layout
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            numero_tablilla = st.text_input(
                "Número de Tablilla",
                placeholder="Ej: 001",
                key=f"input_tablilla_{st.session_state.campo_counter}",
                help="Completa este campo primero"
            )
        
        with col2:
            id_pallet = st.text_input(
                "ID de Pallet",
                placeholder="Ej: PLT001", 
                key=f"input_pallet_{st.session_state.campo_counter}",
                help="El sistema detectará información automáticamente"
            )
            
            # Mostrar información detectada INMEDIATAMENTE cuando cambia el ID
            if id_pallet:
                almacen, codigo, nombre, inv_sistema = buscar_info_pallet(id_pallet, st.session_state.inventario_sistema)
                if almacen is not None:
                    st.markdown(f"""
                    <div class="pallet-info-detected">
                        <strong>✅ Detectado:</strong> {almacen} | {codigo} | {nombre[:50]}{'...' if len(nombre) > 50 else ''} | Sistema: <strong>{inv_sistema}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="pallet-not-found">
                        <strong>⚠️ Pallet no encontrado en el sistema</strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col3:
            cantidad_contada = st.number_input(
                "Cantidad Contada",
                min_value=0,
                step=1,
                key=f"input_cantidad_{st.session_state.campo_counter}",
                help="Presiona Enter aquí para agregar automáticamente"
            )
        
        # Botón para agregar
        if st.button("➕ Agregar al Conteo", use_container_width=True, type="primary"):
            if numero_tablilla and id_pallet:
                # Verificar duplicados
                ids_existentes = [item['id_pallet'] for item in st.session_state.conteo_fisico]
                
                if id_pallet in ids_existentes:
                    # Mostrar modal de duplicado
                    st.session_state.mostrar_duplicado = True
                    st.session_state.pallet_duplicado = id_pallet
                    st.session_state.temp_data = {
                        'numero_tablilla': numero_tablilla,
                        'id_pallet': id_pallet,
                        'cantidad_contada': cantidad_contada
                    }
                    st.rerun()
                else:
                    # Procesar normalmente
                    procesar_pallet(numero_tablilla, id_pallet, cantidad_contada)
                    st.session_state.session_stats['total_processed'] += 1
                    limpiar_campos()
                    st.rerun()
            else:
                st.error("Por favor completa Tablilla e ID de Pallet")
        
        # Modal para manejar duplicados
        if st.session_state.mostrar_duplicado:
            st.markdown("""
            <div class="duplicate-modal">
                <h3>⚠️ DUPLICADO DETECTADO</h3>
                <p>El pallet <strong>{}</strong> ya fue digitado</p>
            </div>
            """.format(st.session_state.pallet_duplicado), unsafe_allow_html=True)
            
            col_dup1, col_dup2, col_dup3 = st.columns(3)
            
            with col_dup1:
                if st.button("🔄 Reemplazar anterior", use_container_width=True):
                    # Remover el existente
                    st.session_state.conteo_fisico = [
                        item for item in st.session_state.conteo_fisico 
                        if item['id_pallet'] != st.session_state.pallet_duplicado
                    ]
                    # Procesar el nuevo
                    procesar_pallet(
                        st.session_state.temp_data['numero_tablilla'],
                        st.session_state.temp_data['id_pallet'],
                        st.session_state.temp_data['cantidad_contada']
                    )
                    st.session_state.mostrar_duplicado = False
                    limpiar_campos()
                    st.rerun()
            
            with col_dup2:
                if st.button("➕ Añadir como nuevo", use_container_width=True):
                    # Procesar como nuevo sin remover
                    procesar_pallet(
                        st.session_state.temp_data['numero_tablilla'],
                        st.session_state.temp_data['id_pallet'],
                        st.session_state.temp_data['cantidad_contada']
                    )
                    st.session_state.mostrar_duplicado = False
                    limpiar_campos()
                    st.rerun()
            
            with col_dup3:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.mostrar_duplicado = False
                    st.rerun()
        
        # Tabla de resultados con funciones de edición
        if st.session_state.conteo_fisico:
            st.subheader("📋 Resultados del Conteo")
            
            # Convertir a DataFrame para mostrar
            df_display = pd.DataFrame(st.session_state.conteo_fisico)
            
            # Agregar índice para selección
            df_display.reset_index(inplace=True)
            df_display.rename(columns={'index': 'row_id'}, inplace=True)
            
            # Formatear diferencias con colores
            def format_diferencia(val):
                if val > 0:
                    return f"🔼 +{val}"
                elif val < 0:
                    return f"🔽 {val}"
                else:
                    return f"✅ {val}"
            
            if 'diferencia' in df_display.columns:
                df_display['diferencia_formatted'] = df_display['diferencia'].apply(format_diferencia)
            
            # Controles de tabla
            col_control1, col_control2, col_control3 = st.columns([2, 1, 1])
            
            with col_control1:
                filtro_busqueda = st.text_input("🔍 Buscar en resultados", placeholder="Buscar por ID, código, producto...")
            
            with col_control2:
                if st.button("✏️ Editar Seleccionado"):
                    if 'registro_seleccionado' in st.session_state and st.session_state.registro_seleccionado is not None:
                        st.session_state.editando = True
                    else:
                        st.warning("Selecciona un registro primero")
            
            with col_control3:
                if st.button("🗑️ Eliminar Seleccionado"):
                    if 'registro_seleccionado' in st.session_state and st.session_state.registro_seleccionado is not None:
                        # Eliminar el registro
                        st.session_state.conteo_fisico.pop(st.session_state.registro_seleccionado)
                        st.session_state.registro_seleccionado = None
                        st.success("Registro eliminado")
                        st.rerun()
                    else:
                        st.warning("Selecciona un registro primero")
            
            # Filtrar datos si hay búsqueda
            df_filtrado = df_display.copy()
            if filtro_busqueda:
                mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(filtro_busqueda, case=False, na=False)).any(axis=1)
                df_filtrado = df_filtrado[mask]
            
            # Selector de registro
            if len(df_filtrado) > 0:
                opciones_registros = []
                for idx, row in df_filtrado.iterrows():
                    opciones_registros.append(f"{row['numero_tablilla']} - {row['id_pallet']} - {row['cantidad_contada']}")
                
                registro_seleccionado = st.selectbox(
                    "Seleccionar registro para editar/eliminar:",
                    options=range(len(opciones_registros)),
                    format_func=lambda x: opciones_registros[x] if x < len(opciones_registros) else "",
                    key="selector_registro"
                )
                
                if registro_seleccionado is not None:
                    st.session_state.registro_seleccionado = df_filtrado.iloc[registro_seleccionado]['row_id']
            
            # Modal de edición
            if st.session_state.editando:
                with st.container():
                    st.subheader("✏️ Editar Registro")
                    
                    # Obtener datos del registro seleccionado
                    registro_actual = st.session_state.conteo_fisico[st.session_state.registro_seleccionado]
                    
                    col_edit1, col_edit2, col_edit3 = st.columns(3)
                    
                    with col_edit1:
                        nueva_tablilla = st.text_input("Número de Tablilla", value=registro_actual['numero_tablilla'])
                    
                    with col_edit2:
                        nuevo_id_pallet = st.text_input("ID de Pallet", value=registro_actual['id_pallet'])
                    
                    with col_edit3:
                        nueva_cantidad = st.number_input("Cantidad Contada", value=registro_actual['cantidad_contada'], min_value=0, step=1)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("💾 Guardar Cambios", use_container_width=True):
                            # Buscar información actualizada del pallet
                            almacen, codigo, nombre, inv_sistema = buscar_info_pallet(nuevo_id_pallet, st.session_state.inventario_sistema)
                            
                            # Calcular nueva diferencia
                            diferencia = nueva_cantidad - (inv_sistema if inv_sistema is not None else 0)
                            
                            # Actualizar registro
                            st.session_state.conteo_fisico[st.session_state.registro_seleccionado].update({
                                'numero_tablilla': nueva_tablilla,
                                'id_pallet': nuevo_id_pallet,
                                'codigo_articulo': codigo if codigo != 'N/A' else '',
                                'nombre_producto': nombre if nombre != 'N/A' else '',
                                'almacen': almacen if almacen != 'N/A' else '',
                                'cantidad_contada': nueva_cantidad,
                                'inv_sistema': inv_sistema,
                                'diferencia': diferencia,
                            })
                            
                            st.session_state.editando = False
                            st.success("Registro actualizado correctamente")
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("❌ Cancelar", use_container_width=True):
                            st.session_state.editando = False
                            st.rerun()
            
            # Mostrar tabla
            st.dataframe(
                df_filtrado[['numero_tablilla', 'id_pallet', 'codigo_articulo', 'nombre_producto', 
                           'almacen', 'cantidad_contada', 'inv_sistema', 'diferencia_formatted']],
                use_container_width=True,
                column_config={
                    'numero_tablilla': 'Tablilla',
                    'id_pallet': 'ID Pallet',
                    'codigo_articulo': 'Código',
                    'nombre_producto': 'Producto',
                    'almacen': 'Almacén',
                    'cantidad_contada': 'Contado',
                    'inv_sistema': 'Sistema',
                    'diferencia_formatted': 'Diferencia'
                }
            )
            
            # Botones de acción
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("🗑️ Limpiar Todo"):
                    st.session_state.conteo_fisico = []
                    st.rerun()
            
            with col2:
                if st.button("📊 Generar Excel"):
                    excel_file = generar_reporte_excel()
                    if excel_file:
                        st.download_button(
                            label="⬇️ Descargar Excel",
                            data=excel_file,
                            file_name=f"Reporte_Inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success("¡Reporte generado!")
            
            with col3:
                if st.button("📈 Actualizar Dashboard"):
                    st.rerun()

# Ejecutar aplicación
if __name__ == "__main__":
    main()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>📦 Visor de Inventario Pro v2.0 - Streamlit Edition</p>
    <p>Desarrollado para optimizar procesos de inventario físico</p>
    <p><em>Funcionalidad completa: Detección en tiempo real, Duplicados, Edición, Dashboard ejecutivo</em></p>
</div>
""", unsafe_allow_html=True)