#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Script de instalación para PythonAnywhere
# Ejecutar en la consola Bash de PythonAnywhere
#
# USO:
#   1. Abre una consola Bash en PythonAnywhere
#   2. Reemplaza TUUSUARIO con tu nombre de usuario real
#   3. Copia y pega este bloque completo
# ══════════════════════════════════════════════════════════════

USUARIO="TUUSUARIO"   # <-- cambia esto por tu username de PythonAnywhere
REPO="https://github.com/jordanrj1/Tsidesk.git"
PROYECTO="Tsidesk"
VENV="$HOME/.virtualenvs/tsidesk"
PYTHON="/usr/bin/python3.12"

echo "=== [1/6] Clonando repositorio ==="
cd ~
git clone "$REPO" "$PROYECTO"
cd "$PROYECTO"

echo "=== [2/6] Creando entorno virtual con Python 3.12 ==="
$PYTHON -m venv "$VENV"
source "$VENV/bin/activate"

echo "=== [3/6] Instalando dependencias ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/6] Variables de entorno ==="
cat > ~/.env_tsidesk << EOF
SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria-de-50-chars
DEBUG=False
ALLOWED_HOSTS=$USUARIO.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://$USUARIO.pythonanywhere.com
EOF
echo "⚠  Edita ~/.env_tsidesk y pon una SECRET_KEY real antes de continuar"

echo "=== [5/6] Migraciones y archivos estáticos ==="
export $(cat ~/.env_tsidesk | xargs)
python manage.py migrate --no-input
python manage.py collectstatic --no-input

echo "=== [6/6] Superusuario ==="
echo "Crea el superusuario manualmente con:"
echo "  source ~/.virtualenvs/tsidesk/bin/activate"
echo "  cd ~/Tsidesk"
echo "  python manage.py createsuperuser"

echo ""
echo "✅ Instalación completa. Ahora configura la Web App en el dashboard (ver instrucciones)."
