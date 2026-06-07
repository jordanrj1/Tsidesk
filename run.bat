@echo off
echo ============================================
echo   TsDesk - Iniciando Servidor
echo ============================================
echo.

call venv\Scripts\activate.bat

echo Servidor iniciado en: http://127.0.0.1:8000
echo.
echo Usuarios:
echo   Admin:      admin / admin123
echo   Secretaria: secretaria / secretaria123
echo.
echo Presione Ctrl+C para detener el servidor.
echo.

python manage.py runserver 0.0.0.0:8000
