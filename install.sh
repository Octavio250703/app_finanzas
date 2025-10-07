#!/bin/bash

# Script de instalación para el Gestor de Inversiones
# Este script automatiza la instalación y configuración inicial

echo "🚀 Iniciando instalación del Gestor de Inversiones..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instala Python 3.8 o superior."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
else
    echo "✅ Entorno virtual ya existe"
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️ Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Verificar instalación
echo "🔍 Verificando instalación..."
python3 -c "import flask, supabase, bcrypt, dotenv; print('✅ Todas las dependencias instaladas correctamente')"

echo ""
echo "🎉 ¡Instalación completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configura tu base de datos Supabase ejecutando el script database_setup.sql"
echo "2. Verifica las credenciales en el archivo .env"
echo "3. Ejecuta la aplicación con: python app.py"
echo "4. Abre tu navegador en: http://localhost:5000"
echo ""
echo "📖 Para más información, consulta el archivo README.md"