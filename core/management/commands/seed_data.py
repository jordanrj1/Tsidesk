"""
Comando de siembra de datos iniciales.
Uso: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import (
    TipoDocumento, Especialidad, CatalogoMaterial,
    Trabajador, Obra, Contrato, BodegaObra
)
from django.utils import timezone
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Carga datos iniciales de demostración en el sistema'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando seed de datos...'))

        # Super Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@empresa.cl', 'admin123')
            self.stdout.write(self.style.SUCCESS('[OK] Super Admin creado (admin/admin123)'))

        # Secretaria
        if not User.objects.filter(username='secretaria').exists():
            u = User.objects.create_user('secretaria', 'secretaria@empresa.cl', 'secretaria123')
            u.first_name = 'Maria'
            u.last_name = 'Gonzalez'
            u.save()
            self.stdout.write(self.style.SUCCESS('[OK] Secretaria creada (secretaria/secretaria123)'))

        # Tipos de Documentos
        docs = [
            ('Cédula de Identidad', 'Trabajador', True),
            ('Certificado AFP', 'Trabajador', True),
            ('Certificado Fonasa', 'Trabajador', True),
            ('Certificado de Antecedentes', 'Trabajador', True),
            ('Contrato de Trabajo Firmado', 'Contrato', True),
            ('Reglamento Interno Firmado', 'Contrato', True),
            ('Finiquito Legalizado', 'Contrato', False),
            ('Anexo de Contrato', 'Contrato', False),
            ('Informe Técnico', 'Obra', False),
            ('Planilla de Cierre Mensual', 'Obra', False),
            ('Estado de Pago Mandante', 'Obra', False),
            ('Acta de Terreno', 'Obra', False),
        ]
        for nombre, nivel, oblig in docs:
            TipoDocumento.objects.get_or_create(nombre=nombre, defaults={'nivel': nivel, 'obligatorio': oblig})
        self.stdout.write(self.style.SUCCESS(f'✓ {len(docs)} tipos de documentos'))

        # Especialidades
        especialidades_data = [
            'Capataz', 'Maestro Primera', 'Maestro Segunda', 'Jornal',
            'Electricista', 'Gasfíter', 'Pintor', 'Fierrero', 'Albañil', 'Carpintero'
        ]
        for esp in especialidades_data:
            Especialidad.objects.get_or_create(nombre=esp)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(especialidades_data)} especialidades'))

        # Materiales
        materiales_data = [
            ('Casco de Seguridad', 10),
            ('Guantes de Trabajo', 20),
            ('Chaleco Reflectante', 10),
            ('Zapatos de Seguridad', 5),
            ('Arnés de Seguridad', 5),
            ('Mascarilla N95', 50),
            ('Gafas de Protección', 10),
            ('Conos de Seguridad', 20),
            ('Cemento (sacos)', 100),
            ('Arena (m3)', 50),
        ]
        for nombre, stock_min in materiales_data:
            CatalogoMaterial.objects.get_or_create(nombre=nombre, defaults={'stock_minimo': stock_min})
        self.stdout.write(self.style.SUCCESS(f'✓ {len(materiales_data)} materiales'))

        # Obras de demo
        esp_capataz = Especialidad.objects.get(nombre='Capataz')
        esp_maestro = Especialidad.objects.get(nombre='Maestro Primera')
        esp_jornal = Especialidad.objects.get(nombre='Jornal')

        obra1, _ = Obra.objects.get_or_create(
            nombre='Hospital Regional Norte',
            defaults={
                'constructora_mandante': 'Constructora Vial S.A.',
                'monto_proyecto': 850000000,
                'fecha_inicio': date(2025, 3, 1),
                'fecha_termino_estimada': date(2026, 3, 31),
                'estado': 'Activa',
            }
        )
        obra2, _ = Obra.objects.get_or_create(
            nombre='Mall Plaza Sur',
            defaults={
                'constructora_mandante': 'Inmobiliaria Central Ltda.',
                'monto_proyecto': 1200000000,
                'fecha_inicio': date(2025, 1, 15),
                'fecha_termino_estimada': date(2026, 6, 30),
                'estado': 'Activa',
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ 2 obras de demo'))

        # Inicializar bodega para obras
        for obra in [obra1, obra2]:
            for mat in CatalogoMaterial.objects.all():
                item, created = BodegaObra.objects.get_or_create(
                    obra=obra, material=mat, defaults={'stock_actual': mat.stock_minimo * 2}
                )

        # Trabajadores de demo
        trabajadores_data = [
            ('12345678-9', 'Carlos', 'Muñoz Rivas', '+56912345678', 'Capataz'),
            ('98765432-1', 'Pedro', 'Soto Araya', '+56987654321', 'Maestro Primera'),
            ('11111111-1', 'Juan', 'Pérez González', '+56911111111', 'Jornal'),
            ('22222222-2', 'Ana', 'Martínez López', '+56922222222', 'Electricista'),
            ('33333333-3', 'Luis', 'Fernández Torres', '+56933333333', 'Jornal'),
        ]

        for rut, nombres, apellidos, telefono, esp_nombre in trabajadores_data:
            t, _ = Trabajador.objects.get_or_create(
                rut=rut,
                defaults={'nombres': nombres, 'apellidos': apellidos, 'telefono': telefono}
            )

            # Crear contrato si no existe
            esp = Especialidad.objects.filter(nombre=esp_nombre).first()
            if esp and not Contrato.objects.filter(trabajador=t, obra=obra1).exists():
                Contrato.objects.create(
                    trabajador=t,
                    obra=obra1,
                    especialidad=esp,
                    sueldo_base=600000 if esp_nombre == 'Jornal' else 900000,
                    fecha_inicio=date(2025, 3, 1),
                    fecha_termino_estimada=date(2026, 1, 31),
                    estado='Vigente',
                )

        self.stdout.write(self.style.SUCCESS(f'✓ {len(trabajadores_data)} trabajadores de demo'))

        self.stdout.write(self.style.SUCCESS('\n=== Seed completado exitosamente ==='))
        self.stdout.write('Accesos:')
        self.stdout.write('  Super Admin:  usuario=admin       contraseña=admin123')
        self.stdout.write('  Secretaria:   usuario=secretaria  contraseña=secretaria123')
        self.stdout.write('  URL:          http://127.0.0.1:8000/login/')
