@echo off
REM Script de instalación para Windows - Gestor de Inversiones

echo 🚀 Iniciando instalación del Gestor de Inversiones...

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado. Por favor instala Python 3.8 o superior.
    echo 📖 Descárgalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python encontrado: %PYTHON_VERSION%

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo 📦 Creando entorno virtual...
    python -m venv venv
) else (
    echo ✅ Entorno virtual ya existe
)

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo ⬆️ Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo 📚 Instalando dependencias...
pip install -r requirements.txt

REM Verificar instalación
echo 🔍 Verificando instalación...
python -c "import flask, supabase, bcrypt, dotenv; print('✅ Todas las dependencias instaladas correctamente')"

echo.
echo 🎉 ¡Instalación completada!
echo.
echo 📋 Próximos pasos:
echo 1. Configura tu base de datos Supabase ejecutando el script database_setup.sql
echo 2. Verifica las credenciales en el archivo .env
echo 3. Ejecuta la aplicación con: python app.py
echo 4. Abre tu navegador en: http://localhost:5000
echo.
echo 📖 Para más información, consulta el archivo README.md
echo.
pause