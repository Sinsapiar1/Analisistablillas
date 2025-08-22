from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import json
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import plotly
import uvicorn

app = FastAPI(title="Visor de Inventario Pro - FastAPI")

# Configurar templates y archivos estáticos
templates = Jinja2Templates(directory="templates")

# Variables globales para el estado de la aplicación
app_state = {
    'inventario_sistema': None,
    'conteo_fisico': [],
    'session_stats': {
        'start_time': datetime.now(),
        'total_processed': 0
    }
}

class InventarioManager:
    """Clase para manejar la lógica del inventario"""
    
    @staticmethod
    def cargar_inventario(archivo_bytes):
        """Carga y procesa el archivo de inventario"""
        try:
            df = pd.read_excel(io.BytesIO(archivo_bytes), dtype=str, engine='openpyxl')
            
            # Limpiar y normalizar
            df = df.dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            
            # Validar columnas requeridas
            required_cols = ['Id de pallet', 'Inventario físico']
            if not all(col in df.columns for col in required_cols):
                return None, f"Faltan columnas requeridas: {required_cols}"
            
            # Crear columnas opcionales
            optional_cols = {
                'Almacén': 'Almacén General',
                'Código de artículo': 'N/A',
                'Nombre del producto': 'Producto sin nombre'
            }
            
            for col, default_val in optional_cols.items():
                if col not in df.columns:
                    df[col] = default_val
            
            # Procesar datos
            df['Inventario físico'] = pd.to_numeric(df['Inventario físico'], errors='coerce').fillna(0).astype(int)
            df['Id de pallet'] = df['Id de pallet'].astype(str).str.strip()
            
            return df, "Archivo cargado exitosamente"
            
        except Exception as e:
            return None, f"Error al cargar archivo: {str(e)}"
    
    @staticmethod
    def buscar_pallet(id_pallet, df_inventario):
        """Busca información del pallet en el inventario"""
        if df_inventario is None or not id_pallet:
            return None
        
        id_clean = str(id_pallet).strip().upper()
        mask = df_inventario['Id de pallet'].astype(str).str.strip().str.upper() == id_clean
        matches = df_inventario[mask]
        
        if not matches.empty:
            match = matches.iloc[0]
            return {
                'found': True,
                'almacen': str(match.get('Almacén', 'N/A')).strip(),
                'codigo': str(match.get('Código de artículo', 'N/A')).strip(),
                'nombre': str(match.get('Nombre del producto', 'N/A')).strip(),
                'inv_sistema': int(float(match.get('Inventario físico', 0)))
            }
        
        return {'found': False}
    
    @staticmethod
    def calcular_estadisticas(conteo_fisico):
        """Calcula estadísticas del conteo"""
        if not conteo_fisico:
            return {
                'total': 0, 'exactos': 0, 'sobrantes': 0, 
                'faltantes': 0, 'no_encontrados': 0, 'precision': 0
            }
        
        df = pd.DataFrame(conteo_fisico)
        total = len(df)
        exactos = len(df[df['diferencia'] == 0])
        sobrantes = len(df[df['diferencia'] > 0])
        faltantes = len(df[df['diferencia'] < 0])
        no_encontrados = len(df[df['inv_sistema'].isna()])
        precision = (exactos / total * 100) if total > 0 else 0
        
        return {
            'total': total, 'exactos': exactos, 'sobrantes': sobrantes,
            'faltantes': faltantes, 'no_encontrados': no_encontrados,
            'precision': round(precision, 2)
        }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""
    stats = InventarioManager.calcular_estadisticas(app_state['conteo_fisico'])
    
    # Crear gráficos
    charts = {}
    
    if stats['total'] > 0:
        # Gráfico de dona
        labels = ['Exactos', 'Sobrantes', 'Faltantes', 'No Encontrados']
        values = [stats['exactos'], stats['sobrantes'], stats['faltantes'], stats['no_encontrados']]
        colors = ['#27ae60', '#f39c12', '#e74c3c', '#9b59b6']
        
        fig_dona = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=.4,
            marker_colors=colors, textinfo='label+percent+value'
        )])
        fig_dona.update_layout(title="Distribución de Resultados", height=400)
        charts['dona'] = json.dumps(fig_dona, cls=PlotlyJSONEncoder)
        
        # Gauge de precisión
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=stats['precision'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Precisión (%)"},
            delta={'reference': 95},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 70], 'color': "lightgray"},
                    {'range': [70, 90], 'color': "yellow"},
                    {'range': [90, 100], 'color': "lightgreen"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 95}
            }
        ))
        fig_gauge.update_layout(height=400)
        charts['gauge'] = json.dumps(fig_gauge, cls=PlotlyJSONEncoder)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "charts": charts,
        "conteo_data": app_state['conteo_fisico'],
        "archivo_cargado": app_state['inventario_sistema'] is not None
    })

@app.post("/upload_inventory")
async def upload_inventory(file: UploadFile = File(...)):
    """Endpoint para cargar archivo de inventario"""
    try:
        contents = await file.read()
        df, message = InventarioManager.cargar_inventario(contents)
        
        if df is not None:
            app_state['inventario_sistema'] = df
            return {"success": True, "message": message, "records": len(df)}
        else:
            return {"success": False, "message": message}
            
    except Exception as e:
        return {"success": False, "message": f"Error procesando archivo: {str(e)}"}

@app.post("/search_pallet")
async def search_pallet(id_pallet: str = Form(...)):
    """Buscar información de un pallet"""
    info = InventarioManager.buscar_pallet(id_pallet, app_state['inventario_sistema'])
    return JSONResponse(info if info else {"found": False})

@app.post("/add_pallet")
async def add_pallet(
    numero_tablilla: str = Form(...),
    id_pallet: str = Form(...),
    cantidad_contada: int = Form(...)
):
    """Agregar pallet al conteo"""
    try:
        # Buscar información del pallet
        pallet_info = InventarioManager.buscar_pallet(id_pallet, app_state['inventario_sistema'])
        
        if pallet_info and pallet_info['found']:
            diferencia = cantidad_contada - pallet_info['inv_sistema']
            inv_sistema = pallet_info['inv_sistema']
            almacen = pallet_info['almacen']
            codigo = pallet_info['codigo']
            nombre = pallet_info['nombre']
        else:
            diferencia = cantidad_contada
            inv_sistema = None
            almacen = 'N/A'
            codigo = 'N/A'
            nombre = 'N/A'
        
        # Crear nuevo registro
        nuevo_item = {
            'numero_tablilla': numero_tablilla,
            'id_pallet': str(id_pallet).strip(),
            'codigo_articulo': codigo,
            'nombre_producto': nombre,
            'almacen': almacen,
            'cantidad_contada': cantidad_contada,
            'inv_sistema': inv_sistema,
            'diferencia': diferencia,
            'timestamp': datetime.now().isoformat(),
            'found_in_system': pallet_info['found'] if pallet_info else False
        }
        
        # Agregar al conteo
        app_state['conteo_fisico'].append(nuevo_item)
        app_state['session_stats']['total_processed'] += 1
        
        # Determinar mensaje de estado
        if pallet_info and pallet_info['found']:
            if diferencia == 0:
                status_msg = f"✅ Cantidad exacta ({cantidad_contada})"
                status_type = "success"
            elif diferencia > 0:
                status_msg = f"🔼 Sobrante de {diferencia} unidades"
                status_type = "warning"
            else:
                status_msg = f"🔽 Faltante de {abs(diferencia)} unidades"
                status_type = "error"
        else:
            status_msg = f"❓ No encontrado - {cantidad_contada} unidades"
            status_type = "info"
        
        return {
            "success": True,
            "message": f"{id_pallet}: {status_msg}",
            "status_type": status_type,
            "stats": InventarioManager.calcular_estadisticas(app_state['conteo_fisico'])
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error agregando pallet: {str(e)}"}

@app.post("/clear_all")
async def clear_all():
    """Limpiar todos los datos"""
    app_state['conteo_fisico'] = []
    app_state['session_stats']['total_processed'] = 0
    return {"success": True, "message": "Datos limpiados"}

@app.get("/export_excel")
async def export_excel():
    """Generar reporte Excel"""
    if not app_state['conteo_fisico']:
        return {"success": False, "message": "No hay datos para exportar"}
    
    try:
        df = pd.DataFrame(app_state['conteo_fisico'])
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Hoja principal
            df.to_excel(writer, sheet_name='Conteo Completo', index=False)
            
            # Hoja de resumen
            stats = InventarioManager.calcular_estadisticas(app_state['conteo_fisico'])
            resumen_data = {
                'Métrica': ['Total Pallets', 'Exactos', 'Sobrantes', 'Faltantes', 'No Encontrados', 'Precisión (%)'],
                'Valor': [stats['total'], stats['exactos'], stats['sobrantes'], 
                         stats['faltantes'], stats['no_encontrados'], stats['precision']]
            }
            pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)
        
        output.seek(0)
        
        # Retornar archivo como respuesta
        from fastapi.responses import StreamingResponse
        
        filename = f"Inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        return {"success": False, "message": f"Error generando Excel: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)