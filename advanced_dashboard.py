import dash
from dash import dcc, html, Input, Output, callback_context, dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# Inicializar la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Ejecutivo de Inventario"

# Datos de ejemplo para demostración
def generate_sample_data():
    """Genera datos de muestra para el dashboard"""
    np.random.seed(42)
    
    # Simular datos de inventario histórico
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    almacenes = ['Almacén A', 'Almacén B', 'Almacén C', 'Almacén D']
    categorias = ['Electrónicos', 'Ropa', 'Hogar', 'Deportes', 'Libros']
    
    data = []
    for date in dates:
        for almacen in almacenes:
            for categoria in categorias:
                precision = np.random.normal(95, 5)  # Precisión promedio 95%
                precision = max(70, min(100, precision))  # Limitar entre 70-100%
                
                total_items = np.random.randint(50, 200)
                exactos = int(total_items * precision / 100)
                diferencias = total_items - exactos
                
                data.append({
                    'fecha': date,
                    'almacen': almacen,
                    'categoria': categoria,
                    'total_items': total_items,
                    'exactos': exactos,
                    'diferencias': diferencias,
                    'precision': precision,
                    'valor_inventario': np.random.uniform(10000, 50000)
                })
    
    return pd.DataFrame(data)

# Cargar datos
df = generate_sample_data()

# Layout del dashboard
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("📊 Dashboard Ejecutivo de Inventario", 
                   className="text-center mb-4",
                   style={'color': '#2c3e50', 'fontWeight': 'bold'}),
            html.Hr()
        ])
    ]),
    
    # Controles de filtro
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 Filtros de Análisis"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Rango de Fechas:"),
                            dcc.DatePickerRange(
                                id='date-range-picker',
                                start_date=df['fecha'].min(),
                                end_date=df['fecha'].max(),
                                display_format='DD/MM/YYYY'
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("Almacenes:"),
                            dcc.Dropdown(
                                id='almacen-dropdown',
                                options=[{'label': alm, 'value': alm} for alm in df['almacen'].unique()],
                                value=df['almacen'].unique().tolist(),
                                multi=True
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("Categorías:"),
                            dcc.Dropdown(
                                id='categoria-dropdown',
                                options=[{'label': cat, 'value': cat} for cat in df['categoria'].unique()],
                                value=df['categoria'].unique().tolist(),
                                multi=True
                            )
                        ], width=4)
                    ])
                ])
            ])
        ])
    ], className="mb-4"),
    
    # KPIs principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id="kpi-precision", className="text-primary"),
                    html.P("Precisión Promedio", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id="kpi-items", className="text-info"),
                    html.P("Items Procesados", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id="kpi-valor", className="text-success"),
                    html.P("Valor Total ($)", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id="kpi-tendencia", className="text-warning"),
                    html.P("Tendencia 7 días", className="text-muted")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Gráficos principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Tendencia de Precisión por Tiempo"),
                dbc.CardBody([
                    dcc.Graph(id="precision-timeline")
                ])
            ])
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎯 Gauge de Performance"),
                dbc.CardBody([
                    dcc.Graph(id="performance-gauge")
                ])
            ])
        ], width=4)
    ], className="mb-4"),
    
    # Análisis avanzado
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🌞 Análisis Sunburst - Jerarquía de Performance"),
                dbc.CardBody([
                    dcc.Graph(id="sunburst-chart")
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔥 Heatmap de Precisión por Almacén/Categoría"),
                dbc.CardBody([
                    dcc.Graph(id="heatmap-chart")
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    # Treemap y análisis detallado
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🗂️ Treemap - Volumen por Categoría"),
                dbc.CardBody([
                    dcc.Graph(id="treemap-chart")
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Waterfall - Análisis de Diferencias"),
                dbc.CardBody([
                    dcc.Graph(id="waterfall-chart")
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    # Tabla de outliers y alertas
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚠️ Alertas y Outliers Críticos"),
                dbc.CardBody([
                    html.Div(id="alerts-table")
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P("Dashboard Ejecutivo - Actualizado en tiempo real", 
                  className="text-center text-muted")
        ])
    ])
], fluid=True)

# Callbacks para actualizar los gráficos
@app.callback(
    [Output('kpi-precision', 'children'),
     Output('kpi-items', 'children'),
     Output('kpi-valor', 'children'),
     Output('kpi-tendencia', 'children')],
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_kpis(start_date, end_date, almacenes, categorias):
    """Actualizar KPIs principales"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    if filtered_df.empty:
        return "0%", "0", "$0", "0%"
    
    precision_avg = filtered_df['precision'].mean()
    total_items = filtered_df['total_items'].sum()
    valor_total = filtered_df['valor_inventario'].sum()
    
    # Calcular tendencia (últimos 7 días vs 7 días anteriores)
    end_date_dt = pd.to_datetime(end_date)
    last_7_days = filtered_df[filtered_df['fecha'] >= (end_date_dt - timedelta(days=7))]
    prev_7_days = filtered_df[
        (filtered_df['fecha'] >= (end_date_dt - timedelta(days=14))) &
        (filtered_df['fecha'] < (end_date_dt - timedelta(days=7)))
    ]
    
    if not prev_7_days.empty:
        tendencia = ((last_7_days['precision'].mean() - prev_7_days['precision'].mean()) / 
                    prev_7_days['precision'].mean() * 100)
        tendencia_str = f"+{tendencia:.1f}%" if tendencia >= 0 else f"{tendencia:.1f}%"
    else:
        tendencia_str = "N/A"
    
    return (
        f"{precision_avg:.1f}%",
        f"{total_items:,}",
        f"${valor_total:,.0f}",
        tendencia_str
    )

@app.callback(
    Output('precision-timeline', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_precision_timeline(start_date, end_date, almacenes, categorias):
    """Crear gráfico de tendencia de precisión"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    # Agrupar por fecha y calcular precisión promedio
    daily_precision = filtered_df.groupby('fecha')['precision'].mean().reset_index()
    
    fig = px.line(daily_precision, x='fecha', y='precision',
                  title="Evolución de la Precisión del Inventario",
                  labels={'precision': 'Precisión (%)', 'fecha': 'Fecha'})
    
    # Agregar línea de objetivo (95%)
    fig.add_hline(y=95, line_dash="dash", line_color="red", 
                  annotation_text="Objetivo: 95%")
    
    # Agregar área de rango aceptable
    fig.add_hrect(y0=90, y1=100, fillcolor="green", opacity=0.1, 
                  annotation_text="Rango Excelente", annotation_position="top left")
    
    fig.update_layout(
        height=400,
        xaxis_title="Fecha",
        yaxis_title="Precisión (%)",
        hovermode='x unified'
    )
    
    return fig

@app.callback(
    Output('performance-gauge', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_performance_gauge(start_date, end_date, almacenes, categorias):
    """Crear gauge de performance"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    precision_avg = filtered_df['precision'].mean() if not filtered_df.empty else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=precision_avg,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Performance General"},
        delta={'reference': 95, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 70], 'color': "lightgray"},
                {'range': [70, 85], 'color': "yellow"},
                {'range': [85, 95], 'color': "orange"},
                {'range': [95, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    
    fig.update_layout(height=400)
    return fig

@app.callback(
    Output('sunburst-chart', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_sunburst_chart(start_date, end_date, almacenes, categorias):
    """Crear gráfico sunburst jerárquico"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    # Preparar datos jerárquicos
    hierarchy_data = []
    
    # Nivel 1: Total
    total_items = filtered_df['total_items'].sum()
    hierarchy_data.append({
        'ids': 'Total',
        'labels': 'Total',
        'parents': '',
        'values': total_items
    })
    
    # Nivel 2: Por almacén
    for almacen in filtered_df['almacen'].unique():
        almacen_data = filtered_df[filtered_df['almacen'] == almacen]
        almacen_items = almacen_data['total_items'].sum()
        
        hierarchy_data.append({
            'ids': almacen,
            'labels': almacen,
            'parents': 'Total',
            'values': almacen_items
        })
        
        # Nivel 3: Por categoría dentro de almacén
        for categoria in almacen_data['categoria'].unique():
            cat_data = almacen_data[almacen_data['categoria'] == categoria]
            cat_items = cat_data['total_items'].sum()
            
            hierarchy_data.append({
                'ids': f"{almacen}-{categoria}",
                'labels': categoria,
                'parents': almacen,
                'values': cat_items
            })
    
    hierarchy_df = pd.DataFrame(hierarchy_data)
    
    fig = go.Figure(go.Sunburst(
        ids=hierarchy_df['ids'],
        labels=hierarchy_df['labels'],
        parents=hierarchy_df['parents'],
        values=hierarchy_df['values'],
        branchvalues="total",
        maxdepth=3
    ))
    
    fig.update_layout(
        title="Jerarquía de Volúmenes: Total → Almacén → Categoría",
        height=400
    )
    
    return fig

@app.callback(
    Output('heatmap-chart', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_heatmap_chart(start_date, end_date, almacenes, categorias):
    """Crear heatmap de precisión"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    # Crear matriz de precisión promedio
    precision_matrix = filtered_df.groupby(['almacen', 'categoria'])['precision'].mean().unstack()
    
    fig = px.imshow(
        precision_matrix.values,
        x=precision_matrix.columns,
        y=precision_matrix.index,
        color_continuous_scale='RdYlGn',
        aspect="auto",
        title="Mapa de Calor: Precisión por Almacén y Categoría"
    )
    
    fig.update_layout(
        xaxis_title="Categorías",
        yaxis_title="Almacenes",
        height=400
    )
    
    return fig

@app.callback(
    Output('treemap-chart', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_treemap_chart(start_date, end_date, almacenes, categorias):
    """Crear treemap de volúmenes"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    # Agrupar por categoría y almacén
    treemap_data = filtered_df.groupby(['categoria', 'almacen']).agg({
        'total_items': 'sum',
        'precision': 'mean',
        'valor_inventario': 'sum'
    }).reset_index()
    
    fig = px.treemap(
        treemap_data,
        path=['categoria', 'almacen'],
        values='total_items',
        color='precision',
        color_continuous_scale='RdYlGn',
        title="Treemap: Volumen de Items por Categoría y Almacén"
    )
    
    fig.update_layout(height=400)
    return fig

@app.callback(
    Output('waterfall-chart', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_waterfall_chart(start_date, end_date, almacenes, categorias):
    """Crear gráfico waterfall de diferencias"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    # Calcular diferencias por almacén
    diferencias_almacen = filtered_df.groupby('almacen')['diferencias'].sum()
    
    # Crear datos para waterfall
    x_values = ['Inicio'] + list(diferencias_almacen.index) + ['Total Final']
    y_values = [0] + list(diferencias_almacen.values) + [diferencias_almacen.sum()]
    
    fig = go.Figure(go.Waterfall(
        name="Diferencias",
        orientation="v",
        measure=["absolute"] + ["relative"] * len(diferencias_almacen) + ["total"],
        x=x_values,
        textposition="outside",
        text=[f"+{v}" if v > 0 else str(v) for v in y_values],
        y=y_values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title="Análisis Waterfall: Flujo de Diferencias por Almacén",
        height=400,
        showlegend=False
    )
    
    return fig

@app.callback(
    Output('alerts-table', 'children'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('almacen-dropdown', 'value'),
     Input('categoria-dropdown', 'value')]
)
def update_alerts_table(start_date, end_date, almacenes, categorias):
    """Generar tabla de alertas y outliers"""
    filtered_df = df[
        (df['fecha'] >= start_date) & 
        (df['fecha'] <= end_date) &
        (df['almacen'].isin(almacenes)) &
        (df['categoria'].isin(categorias))
    ]
    
    # Identificar outliers (precisión < 85% o diferencias > 20%)
    alerts = []
    
    for _, row in filtered_df.iterrows():
        if row['precision'] < 85:
            alerts.append({
                'Tipo': '🔴 Precisión Crítica',
                'Almacén': row['almacen'],
                'Categoría': row['categoria'],
                'Fecha': row['fecha'].strftime('%d/%m/%Y'),
                'Valor': f"{row['precision']:.1f}%",
                'Descripción': 'Precisión por debajo del umbral crítico'
            })
        
        if row['diferencias'] > 20:
            alerts.append({
                'Tipo': '⚠️ Alto Volumen de Diferencias',
                'Almacén': row['almacen'],
                'Categoría': row['categoria'],
                'Fecha': row['fecha'].strftime('%d/%m/%Y'),
                'Valor': f"{row['diferencias']} items",
                'Descripción': 'Volumen de diferencias superior al normal'
            })
    
    if not alerts:
        return dbc.Alert("✅ No se detectaron alertas críticas en el período seleccionado", 
                        color="success")
    
    alerts_df = pd.DataFrame(alerts)
    
    return dash_table.DataTable(
        data=alerts_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in alerts_df.columns],
        style_cell={'textAlign': 'left', 'fontSize': 12},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{Tipo} contains "🔴"'},
                'backgroundColor': '#ffebee',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{Tipo} contains "⚠️"'},
                'backgroundColor': '#fff3e0',
                'color': 'black',
            }
        ],
        page_size=10,
        sort_action="native",
        filter_action="native"
    )

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)