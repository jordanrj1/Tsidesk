from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone


MAX_INTENTOS = 5        # intentos fallidos permitidos
BLOQUEO_SEGUNDOS = 300  # 5 minutos de bloqueo


class LoginBruteForceMiddleware:
    """
    Bloquea una IP por 5 minutos después de 5 intentos fallidos de login.
    No requiere dependencias externas — usa la caché de Django.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.path == '/login/':
            ip = self._get_ip(request)
            clave_bloqueo = f'login_bloqueado_{ip}'
            clave_intentos = f'login_intentos_{ip}'

            if cache.get(clave_bloqueo):
                segundos = cache.ttl(clave_bloqueo) if hasattr(cache, 'ttl') else BLOQUEO_SEGUNDOS
                return HttpResponse(
                    f'<html><body style="font-family:sans-serif;text-align:center;padding:60px">'
                    f'<h2>⛔ Acceso bloqueado temporalmente</h2>'
                    f'<p>Demasiados intentos fallidos. Espera <strong>5 minutos</strong> e intenta de nuevo.</p>'
                    f'<p style="color:#888;font-size:.9em">Si crees que es un error, contacta al administrador.</p>'
                    f'</body></html>',
                    status=429,
                )

        response = self.get_response(request)

        # Detecta login fallido: Django redirige al mismo /login/ con form errors
        if (request.method == 'POST' and request.path == '/login/'
                and response.status_code == 200):
            ip = self._get_ip(request)
            clave_intentos = f'login_intentos_{ip}'
            intentos = (cache.get(clave_intentos) or 0) + 1
            cache.set(clave_intentos, intentos, BLOQUEO_SEGUNDOS)
            if intentos >= MAX_INTENTOS:
                cache.set(f'login_bloqueado_{ip}', True, BLOQUEO_SEGUNDOS)
                cache.delete(clave_intentos)

        # Login exitoso: limpia contadores
        if (request.method == 'POST' and request.path == '/login/'
                and response.status_code == 302):
            ip = self._get_ip(request)
            cache.delete(f'login_intentos_{ip}')
            cache.delete(f'login_bloqueado_{ip}')

        return response

    def _get_ip(self, request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
