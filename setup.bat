@echo off
echo ============================================
echo   TsDesk - Instalacion del Sistema
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado. Instale Python 3.10+ desde python.org
    pause
    exit /b 1
)

echo [1/5] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)

echo [2/5] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [3/5] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Fallo la instalacion de dependencias
    pause
    exit /b 1
)

echo [4/5] Ejecutando migraciones de base de datos...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Fallo la migracion
    pause
    exit /b 1
)

echo [5/5] Cargando datos iniciales de demostracion...
python manage.py seed_data

echo.
echo ============================================
echo   Instalacion completada exitosamente!
echo ============================================
echo.
echo Para iniciar el servidor, ejecute: run.bat
echo O manualmente:
echo   venv\Scripts\activate
echo   python manage.py runserver
echo.
pause
