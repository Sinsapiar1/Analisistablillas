#!/bin/bash

# Script de inicio para Visor de Inventario Pro
# Permite seleccionar qué versión de la aplicación ejecutar

echo "🚀 Iniciando Visor de Inventario Pro"
echo "======================================="

# Verificar variable de entorno APP_TYPE
case "${APP_TYPE:-fastapi}" in
    "fastapi")
        echo "📡 Iniciando FastAPI + HTML/JS (Navegación Perfecta)"
        echo "URL: http://localhost:8000"
        exec python fastapi_app.py
        ;;
    "streamlit")
        echo "🌊 Iniciando Streamlit Mejorado"
        echo "URL: http://localhost:8501"
        exec streamlit run app_improved.py --server.address=0.0.0.0 --server.port=8501
        ;;
    "dashboard")
        echo "📊 Iniciando Dashboard Ejecutivo (Dash)"
        echo "URL: http://localhost:8050"
        exec python advanced_dashboard.py
        ;;
    *)
        echo "❌ APP_TYPE no válido. Opciones: fastapi, streamlit, dashboard"
        echo "🔧 Usando FastAPI por defecto..."
        exec python fastapi_app.py
        ;;
esac