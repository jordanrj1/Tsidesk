# ══════════════════════════════════════════════════════════════
# Archivo WSGI para PythonAnywhere
#
# INSTRUCCIONES:
#   1. En el dashboard de PythonAnywhere → pestaña "Web"
#   2. Haz clic en el link del archivo WSGI
#      (algo como /var/www/TUUSUARIO_pythonanywhere_com_wsgi.py)
#   3. Borra TODO el contenido existente
#   4. Pega este archivo completo
#   5. Cambia TUUSUARIO por tu username real
#   6. Cambia la SECRET_KEY por una clave real
# ══════════════════════════════════════════════════════════════

import sys
import os

# ── Ruta del proyecto ──────────────────────────────────────────
USUARIO = 'TUUSUARIO'   # <-- cambia esto
path = f'/home/{USUARIO}/Tsidesk'
if path not in sys.path:
    sys.path.insert(0, path)

# ── Variables de entorno ───────────────────────────────────────
os.environ['DJANGO_SETTINGS_MODULE'] = 'tsidesk_project.settings'
os.environ['SECRET_KEY']             = 'PON-AQUI-UNA-CLAVE-LARGA-Y-ALEATORIA'
os.environ['DEBUG']                  = 'False'
os.environ['ALLOWED_HOSTS']          = f'{USUARIO}.pythonanywhere.com'
os.environ['CSRF_TRUSTED_ORIGINS']   = f'https://{USUARIO}.pythonanywhere.com'

# ── Aplicación WSGI ────────────────────────────────────────────
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
