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
    page_title="Visor de Inventario Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado y JavaScript para mejorar la digitación
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .success-card {
        border-left-color: #27ae60;
    }
    .warning-card {
        border-left-color: #f39c12;
    }
    .danger-card {
        border-left-color: #e74c3c;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    .digitacion-rapida {
        background: rgba(0, 123, 255, 0.1);
        border: 2px solid #007bff;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .campo-activo {
        background: rgba(40, 167, 69, 0.1);
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
    }
    .campo-completado {
        background: rgba(40, 167, 69, 0.2);
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
    }
    .input-focus {
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
    }
</style>

<script>
function autoFocusInput() {
    // Buscar el input visible y hacer focus
    setTimeout(() => {
        const inputs = document.querySelectorAll('input[type="text"], input[type="number"]');
        const visibleInputs = Array.from(inputs).filter(input => {
            const rect = input.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        });
        
        if (visibleInputs.length > 0) {
            const lastInput = visibleInputs[visibleInputs.length - 1];
            lastInput.focus();
            lastInput.select();
        }
    }, 100);
}

// Ejecutar cuando la página se carga
document.addEventListener('DOMContentLoaded', autoFocusInput);

// Ejecutar cuando Streamlit actualiza el contenido
window.addEventListener('load', autoFocusInput);

// Observer para detectar cambios en el DOM
const observer = new MutationObserver(autoFocusInput);
observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Inicializar estado de la sesión
if 'inventario_sistema' not in st.session_state:
    st.session_state.inventario_sistema = None
if 'conteo_fisico' not in st.session_state:
    st.session_state.conteo_fisico = []
if 'archivo_cargado' not in st.session_state:
    st.session_state.archivo_cargado = False

# Funciones auxiliares
def cargar_inventario(archivo):
    """Carga y valida el archivo de inventario"""
    try:
        # Leer archivo Excel
        df = pd.read_excel(archivo, dtype=str, engine='openpyxl')
        
        # Normalizar nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        
        # Validar columnas requeridas
        required_cols = ['Id de pallet', 'Inventario físico']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"La columna requerida '{col}' no se encontró en el archivo.")
                return None
        
        # Crear columna Almacén si no existe
        if 'Almacén' not in df.columns:
            df['Almacén'] = 'Almacén General'
            st.warning("No se encontró columna 'Almacén'. Se asignará 'Almacén General' por defecto.")
        
        # Procesar columnas
        df['Inventario físico'] = pd.to_numeric(df['Inventario físico'], errors='coerce').fillna(0).astype(int)
        
        # Verificar duplicados
        dup_count = df['Id de pallet'].duplicated().sum()
        if dup_count > 0:
            st.warning(f"Se detectaron {dup_count} IDs de pallet duplicados en el inventario del sistema.")
        
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
    # Usar info detectada si está disponible
    if 'info_detectada' in st.session_state and st.session_state.info_detectada:
        info = st.session_state.info_detectada
        almacen = info['almacen']
        codigo = info['codigo'] 
        nombre = info['nombre']
        inv_sistema = info['inv_sistema']
    else:
        # Buscar información del pallet nuevamente
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
    st.success(f"Pallet {id_pallet} agregado correctamente")

def limpiar_campos():
    """Función para limpiar los campos de entrada usando keys dinámicas"""
    # En lugar de modificar los valores directamente, usamos un contador para generar nuevas keys
    if 'campo_counter' not in st.session_state:
        st.session_state.campo_counter = 0
    st.session_state.campo_counter += 1

def generar_reporte_excel():
    """Genera reporte profesional en formato Excel con múltiples hojas y formato avanzado"""
    if not st.session_state.conteo_fisico:
        return None
    
    # Crear DataFrame del conteo
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
        # Recalcular diferencias para asegurar consistencia
        encontrados['diferencia_calc'] = encontrados['cantidad_contada'] - encontrados['inv_sistema']
        diferencias = encontrados[encontrados['diferencia_calc'] != 0].copy()
        exactos = encontrados[encontrados['diferencia_calc'] == 0].copy()
    else:
        diferencias = pd.DataFrame()
        exactos = pd.DataFrame()
    
    # Crear archivo Excel en memoria con formato profesional
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formatos profesionales
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': '#2c3e50',
            'align': 'center'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#3498db',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })
        
        difference_format = workbook.add_format({
            'bg_color': '#f8d7da',
            'font_color': '#721c24',
            'border': 1
        })
        
        exact_format = workbook.add_format({
            'bg_color': '#d4edda',
            'font_color': '#155724',
            'border': 1
        })
        
        normal_format = workbook.add_format({'border': 1})
        
        # === HOJA 1: RESUMEN EJECUTIVO ===
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
                len(diferencias[diferencias['diferencia_calc'] > 0]) if not diferencias.empty else 0,
                len(diferencias[diferencias['diferencia_calc'] < 0]) if not diferencias.empty else 0
            ]
        }
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False, startrow=2)
        
        ws_resumen = writer.sheets['Resumen Ejecutivo']
        ws_resumen.write('A1', 'REPORTE DE INVENTARIO FÍSICO', title_format)
        ws_resumen.set_column('A:A', 30)
        ws_resumen.set_column('B:B', 25)
        
        # === HOJA 2: DISCREPANCIAS ===
        if not diferencias.empty:
            cols_diferencias = ['numero_tablilla', 'id_pallet', 'almacen', 'codigo_articulo', 
                               'nombre_producto', 'cantidad_contada', 'inv_sistema', 'diferencia_calc']
            
            # Renombrar columnas para el reporte
            diferencias_export = diferencias[cols_diferencias].copy()
            diferencias_export.columns = ['Tablilla', 'ID Pallet', 'Almacén', 'Código', 
                                         'Producto', 'Contado', 'Sistema', 'Diferencia']
            
            diferencias_export.to_excel(writer, sheet_name='Discrepancias', index=False, startrow=1)
            ws_diff = writer.sheets['Discrepancias']
            ws_diff.write('A1', 'DISCREPANCIAS DE INVENTARIO', title_format)
            
            # Aplicar formato condicional
            for row_num in range(2, len(diferencias_export) + 2):
                for col_num in range(len(diferencias_export.columns)):
                    cell_format = difference_format if diferencias_export.iloc[row_num-2, -1] != 0 else normal_format
                    ws_diff.write(row_num, col_num, diferencias_export.iloc[row_num-2, col_num], cell_format)
        
        # === HOJA 3: CANTIDADES EXACTAS ===
        if not exactos.empty:
            cols_exactos = ['numero_tablilla', 'id_pallet', 'almacen', 'codigo_articulo', 
                           'nombre_producto', 'cantidad_contada']
            
            exactos_export = exactos[cols_exactos].copy()
            exactos_export.columns = ['Tablilla', 'ID Pallet', 'Almacén', 'Código', 'Producto', 'Cantidad']
            
            exactos_export.to_excel(writer, sheet_name='Cantidades Exactas', index=False, startrow=1)
            ws_exact = writer.sheets['Cantidades Exactas']
            ws_exact.write('A1', 'CANTIDADES EXACTAS', title_format)
            
            # Aplicar formato de exactos
            for row_num in range(2, len(exactos_export) + 2):
                for col_num in range(len(exactos_export.columns)):
                    ws_exact.write(row_num, col_num, exactos_export.iloc[row_num-2, col_num], exact_format)
        
        # === HOJA 4: NO ENCONTRADOS ===
        if not no_encontrados.empty:
            cols_no_encontrados = ['numero_tablilla', 'id_pallet', 'almacen', 'cantidad_contada']
            
            no_encontrados_export = no_encontrados[cols_no_encontrados].copy()
            no_encontrados_export.columns = ['Tablilla', 'ID Pallet', 'Almacén', 'Cantidad']
            
            no_encontrados_export.to_excel(writer, sheet_name='No Encontrados', index=False, startrow=1)
            ws_nf = writer.sheets['No Encontrados']
            ws_nf.write('A1', 'PALLETS NO ENCONTRADOS EN SISTEMA', title_format)
        
        # === HOJA 5: ANÁLISIS POR ALMACÉN ===
        if 'almacen' in df_conteo.columns:
            analisis_almacen = df_conteo.groupby('almacen').agg({
                'id_pallet': 'count',
                'cantidad_contada': 'sum'
            }).reset_index()
            analisis_almacen.columns = ['Almacén', 'Cantidad Pallets', 'Total Unidades']
            
            analisis_almacen.to_excel(writer, sheet_name='Análisis por Almacén', index=False, startrow=1)
            ws_alm = writer.sheets['Análisis por Almacén']
            ws_alm.write('A1', 'ANÁLISIS POR ALMACÉN', title_format)
    
    output.seek(0)
    return output

# Header principal
st.markdown("""
<div class="main-header">
    <h1>📦 Visor de Inventario Pro v2.0 - Streamlit</h1>
    <p>Sistema avanzado de análisis de inventarios físicos</p>
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

# Contenido principal
if not st.session_state.archivo_cargado:
    st.info("👆 Para comenzar, carga un archivo de inventario en el panel lateral")
    
    # Mostrar ejemplo de estructura esperada
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
    
    # Digitación con Enter en cantidad para agregar automáticamente
    st.subheader("Digitación de Conteo Físico")
    
    # JavaScript para Enter en campo cantidad
    st.markdown("""
    <script>
    function setupQuantityEnter() {
        setTimeout(() => {
            const quantityInputs = document.querySelectorAll('input[type="number"]');
            
            quantityInputs.forEach(input => {
                // Remover listener anterior si existe
                input.removeEventListener('keydown', handleQuantityEnter);
                
                // Agregar nuevo listener
                input.addEventListener('keydown', handleQuantityEnter);
            });
        }, 300);
    }
    
    function handleQuantityEnter(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            
            // Buscar el botón "Agregar al Conteo"
            const addButton = document.querySelector('button[kind="primary"]');
            if (addButton && addButton.textContent.includes('Agregar')) {
                addButton.click();
            }
        }
    }
    
    // Ejecutar al cargar y después de actualizaciones
    document.addEventListener('DOMContentLoaded', setupQuantityEnter);
    window.addEventListener('load', setupQuantityEnter);
    
    // Observer para cambios en el DOM
    const observer = new MutationObserver(setupQuantityEnter);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
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
                st.success(f"Detectado: {almacen} | {codigo} | {nombre[:50]}... | Sistema: {inv_sistema}")
                # Guardar la info detectada en session_state para usarla después
                st.session_state.info_detectada = {
                    'almacen': almacen,
                    'codigo': codigo, 
                    'nombre': nombre,
                    'inv_sistema': inv_sistema
                }
            else:
                st.warning("Pallet no encontrado en el sistema")
                st.session_state.info_detectada = None
        else:
            st.session_state.info_detectada = None
    
    with col3:
        cantidad_contada = st.number_input(
            "Cantidad Contada",
            min_value=0,
            step=1,
            key=f"input_cantidad_{st.session_state.campo_counter}",
            help="PRESIONA ENTER AQUÍ PARA AGREGAR AUTOMÁTICAMENTE"
        )
    
    # Botón para agregar
    if st.button("Agregar al Conteo", use_container_width=True, type="primary"):
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
                # Limpiar campos generando nuevas keys
                limpiar_campos()
                st.rerun()
        else:
            st.error("Por favor completa Tablilla e ID de Pallet")
    
    # Modal para manejar duplicados
    if 'mostrar_duplicado' in st.session_state and st.session_state.mostrar_duplicado:
        st.error(f"DUPLICADO DETECTADO: El pallet {st.session_state.pallet_duplicado} ya fue digitado")
        
        col_dup1, col_dup2, col_dup3 = st.columns(3)
        
        with col_dup1:
            if st.button("Reemplazar anterior", use_container_width=True):
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
                # Limpiar
                st.session_state.mostrar_duplicado = False
                limpiar_campos()
                st.rerun()
        
        with col_dup2:
            if st.button("Añadir como nuevo", use_container_width=True):
                # Procesar como nuevo sin remover
                procesar_pallet(
                    st.session_state.temp_data['numero_tablilla'],
                    st.session_state.temp_data['id_pallet'],
                    st.session_state.temp_data['cantidad_contada']
                )
                # Limpiar
                st.session_state.mostrar_duplicado = False
                limpiar_campos()
                st.rerun()
        
        with col_dup3:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.mostrar_duplicado = False
                st.rerun()
    
    # Instrucciones actualizadas
    st.info("Flujo: Tablilla → Tab → ID Pallet (verás info detectada) → Tab → Cantidad → **ENTER PARA AGREGAR**")
    
    # Re-ejecutar setup para asegurar que funcione
    st.markdown('<script>setupQuantityEnter();</script>', unsafe_allow_html=True)
    
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
        if 'editando' in st.session_state and st.session_state.editando:
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
            excel_file = generar_reporte_excel()
            if excel_file:
                st.download_button(
                    label="📊 Descargar Excel",
                    data=excel_file,
                    file_name=f"Reporte_Inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col3:
            if st.button("📈 Ver Análisis"):
                st.rerun()
        
        # Análisis avanzado con múltiples visualizaciones
        if total > 0:
            st.subheader("Análisis Visual Avanzado")
            
            # Crear pestañas para diferentes análisis
            tab1, tab2, tab3, tab4 = st.tabs(["Dashboard Principal", "Análisis por Almacén", "Análisis de Diferencias", "Métricas Detalladas"])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de dona mejorado - Distribución de resultados
                    labels = ['Exactos', 'Sobrantes', 'Faltantes', 'No Encontrados']
                    values = [exactos, sobrantes, faltantes, no_encontrados]
                    colors = ['#27ae60', '#f39c12', '#e74c3c', '#9b59b6']
                    
                    fig_dona = go.Figure(data=[go.Pie(
                        labels=labels, 
                        values=values, 
                        hole=.4,
                        marker_colors=colors,
                        textinfo='label+percent+value',
                        textfont_size=12
                    )])
                    fig_dona.update_layout(
                        title="Distribución de Resultados",
                        title_font_size=16,
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="middle", y=0.5)
                    )
                    st.plotly_chart(fig_dona, use_container_width=True)
                
                with col2:
                    # Gráfico de KPIs principales
                    precision = (exactos / total * 100) if total > 0 else 0
                    
                    fig_kpis = go.Figure()
                    
                    # Gauge de precisión
                    fig_kpis.add_trace(go.Indicator(
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
                    
                    fig_kpis.update_layout(height=400)
                    st.plotly_chart(fig_kpis, use_container_width=True)
            
            with tab2:
                # Análisis por almacén
                if 'almacen' in df_display.columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de barras - Cantidad por almacén
                        almacen_counts = df_display['almacen'].value_counts()
                        
                        fig_bar = px.bar(
                            x=almacen_counts.values,
                            y=almacen_counts.index,
                            orientation='h',
                            title="Pallets por Almacén",
                            labels={'x': 'Cantidad de Pallets', 'y': 'Almacén'},
                            color=almacen_counts.values,
                            color_continuous_scale='Blues'
                        )
                        fig_bar.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    with col2:
                        # Análisis de precisión por almacén
                        almacen_analysis = df_display.groupby('almacen').agg({
                            'id_pallet': 'count',
                            'diferencia': lambda x: (x == 0).sum()
                        }).reset_index()
                        almacen_analysis['precision'] = (almacen_analysis['diferencia'] / almacen_analysis['id_pallet'] * 100).round(2)
                        almacen_analysis.columns = ['Almacén', 'Total Pallets', 'Exactos', 'Precisión (%)']
                        
                        fig_precision = px.bar(
                            almacen_analysis,
                            x='Almacén',
                            y='Precisión (%)',
                            title="Precisión por Almacén",
                            color='Precisión (%)',
                            color_continuous_scale='RdYlGn',
                            text='Precisión (%)'
                        )
                        fig_precision.update_traces(texttemplate='%{text}%', textposition='outside')
                        fig_precision.update_layout(height=400)
                        st.plotly_chart(fig_precision, use_container_width=True)
                        
                        # Tabla de resumen por almacén
                        st.subheader("Resumen por Almacén")
                        st.dataframe(almacen_analysis, use_container_width=True)
            
            with tab3:
                # Análisis detallado de diferencias
                if 'diferencia' in df_display.columns:
                    diferencias_data = df_display[df_display['diferencia'] != 0].copy() if len(df_display[df_display['diferencia'] != 0]) > 0 else pd.DataFrame()
                    
                    if not diferencias_data.empty:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Histograma de diferencias
                            fig_hist = px.histogram(
                                diferencias_data,
                                x='diferencia',
                                title="Distribución de Diferencias",
                                labels={'diferencia': 'Diferencia', 'count': 'Frecuencia'},
                                color_discrete_sequence=['#e74c3c']
                            )
                            fig_hist.update_layout(height=400)
                            st.plotly_chart(fig_hist, use_container_width=True)
                        
                        with col2:
                            # Scatter plot: Cantidad contada vs Sistema
                            fig_scatter = px.scatter(
                                df_display,
                                x='inv_sistema',
                                y='cantidad_contada',
                                color='diferencia',
                                title="Cantidad Contada vs Sistema",
                                labels={'inv_sistema': 'Inventario Sistema', 'cantidad_contada': 'Cantidad Contada'},
                                color_continuous_scale='RdYlBu'
                            )
                            # Línea de referencia (perfecta coincidencia)
                            max_val = max(df_display['inv_sistema'].max(), df_display['cantidad_contada'].max())
                            fig_scatter.add_shape(
                                type="line",
                                x0=0, y0=0, x1=max_val, y1=max_val,
                                line=dict(color="gray", width=2, dash="dash")
                            )
                            fig_scatter.update_layout(height=400)
                            st.plotly_chart(fig_scatter, use_container_width=True)
                        
                        # Top 10 mayores diferencias
                        st.subheader("Top 10 Mayores Diferencias")
                        top_diferencias = diferencias_data.nlargest(10, 'diferencia')[
                            ['id_pallet', 'almacen', 'cantidad_contada', 'inv_sistema', 'diferencia']
                        ]
                        st.dataframe(top_diferencias, use_container_width=True)
                    else:
                        st.info("No hay diferencias para analizar - ¡Excelente precisión!")
            
            with tab4:
                # Métricas detalladas y estadísticas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Tasa de Error", 
                        f"{((total - exactos) / total * 100):.2f}%" if total > 0 else "0%",
                        delta=f"-{((exactos) / total * 100):.2f}%" if total > 0 else "0%"
                    )
                    
                    st.metric(
                        "Varianza Promedio",
                        f"{df_display['diferencia'].var():.2f}" if len(df_display) > 0 else "0",
                        help="Variabilidad en las diferencias"
                    )
                
                with col2:
                    total_unidades_contadas = df_display['cantidad_contada'].sum() if len(df_display) > 0 else 0
                    total_unidades_sistema = df_display['inv_sistema'].sum() if len(df_display) > 0 else 0
                    
                    st.metric(
                        "Total Unidades Contadas",
                        f"{total_unidades_contadas:,}",
                        delta=f"{total_unidades_contadas - total_unidades_sistema:+,}" if total_unidades_sistema > 0 else "0"
                    )
                    
                    st.metric(
                        "Eficiencia de Conteo",
                        f"{(total / (total + no_encontrados) * 100):.1f}%" if (total + no_encontrados) > 0 else "100%",
                        help="Porcentaje de pallets válidos vs total intentado"
                    )
                
                with col3:
                    promedio_diferencia = df_display['diferencia'].mean() if len(df_display) > 0 else 0
                    st.metric(
                        "Diferencia Promedio",
                        f"{promedio_diferencia:.2f}",
                        delta=f"{'↑' if promedio_diferencia > 0 else '↓'}"
                    )
                    
                    st.metric(
                        "Pallets Críticos",
                        len(df_display[abs(df_display['diferencia']) > 10]) if len(df_display) > 0 else 0,
                        help="Pallets con diferencias > 10 unidades"
                    )
                
                # Estadísticas descriptivas
                if len(df_display) > 0:
                    st.subheader("Estadísticas Descriptivas")
                    stats_df = df_display[['cantidad_contada', 'inv_sistema', 'diferencia']].describe()
                    st.dataframe(stats_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>📦 Visor de Inventario Pro v2.0 - Streamlit Edition</p>
    <p>Desarrollado para optimizar procesos de inventario físico</p>
</div>
""", unsafe_allow_html=True)