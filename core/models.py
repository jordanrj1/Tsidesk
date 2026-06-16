from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os, re, uuid


def _safe_name(name, maxlen=50):
    """Convierte un string a nombre seguro para carpetas del sistema de archivos."""
    name = re.sub(r'[^\w\s\-\.]', '', name, flags=re.UNICODE)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:maxlen] or 'sin_nombre'


def documento_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    tipo = _safe_name(instance.tipo_documento.nombre) if instance.tipo_documento else 'DOC'
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')

    if instance.contrato_id:
        # Documento de contrato → obras/{nombre_obra}/trabajadores/{rut}/
        try:
            contrato = instance.contrato
            obra_nombre = _safe_name(contrato.obra.nombre) if contrato.obra else f'obra_{instance.contrato.obra_id}'
            rut = str(contrato.trabajador_id)
        except Exception:
            obra_nombre = 'sin_obra'
            rut = 'sin_rut'
        folder = os.path.join('documentos', 'obras', obra_nombre, 'trabajadores', rut)
        new_name = f"{tipo}_{ts}.{ext}"

    elif instance.obra_id and not instance.trabajador_rut:
        # Documento de nivel Obra → obras/{nombre_obra}/carpeta/
        try:
            obra_nombre = _safe_name(instance.obra.nombre) if instance.obra else f'obra_{instance.obra_id}'
        except Exception:
            obra_nombre = f'obra_{instance.obra_id}'
        folder = os.path.join('documentos', 'obras', obra_nombre, 'carpeta')
        new_name = f"{tipo}_{ts}.{ext}"

    else:
        # Documento personal del trabajador → trabajadores/{rut}/
        rut = instance.trabajador_rut or 'sin_rut'
        folder = os.path.join('documentos', 'trabajadores', rut)
        new_name = f"{tipo}_{ts}.{ext}"

    return os.path.join(folder, new_name)


def cierre_upload_path(instance, filename):
    """Cierres mensuales → cierres/{nombre_obra}/{filename}"""
    try:
        obra_nombre = _safe_name(instance.obra.nombre) if instance.obra else f'obra_{instance.obra_id}'
    except Exception:
        obra_nombre = f'obra_{instance.obra_id}'
    return os.path.join('cierres', obra_nombre, filename)


# ---------------------------------------------------------------------------
# CATÁLOGOS
# ---------------------------------------------------------------------------

class TipoDocumento(models.Model):
    NIVEL_CHOICES = [('Trabajador', 'Trabajador'), ('Contrato', 'Contrato'), ('Obra', 'Obra')]
    nombre = models.CharField(max_length=100, unique=True)
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    obligatorio = models.BooleanField(default=False)
    # Días de validez desde la fecha de carga. NULL = no vence nunca.
    dias_validez = models.IntegerField(null=True, blank=True, help_text='Días de vigencia desde la carga. Vacío = no vence.')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'
        ordering = ['nivel', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.nivel})"


class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class CatalogoMaterial(models.Model):
    CATEGORIA_CHOICES = [
        ('EPP', 'EPP / Protección Personal'),
        ('ENFIERRADURA', 'Enfierradura'),
        ('CONSTRUCCION', 'Materiales de Construcción'),
        ('HERRAMIENTAS', 'Herramientas'),
        ('ELECTRICO', 'Materiales Eléctricos'),
        ('OTROS', 'Otros'),
    ]
    UNIDAD_CHOICES = [
        ('unid', 'Unidad'),
        ('par', 'Par'),
        ('kg', 'Kilogramo'),
        ('lts', 'Litros'),
        ('m', 'Metro'),
        ('m2', 'Metro cuadrado'),
        ('m3', 'Metro cúbico'),
        ('rollo', 'Rollo'),
        ('caja', 'Caja'),
        ('saco', 'Saco'),
        ('gl', 'Galón'),
    ]
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=200, blank=True, default='')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='OTROS')
    unidad_medida = models.CharField(max_length=10, choices=UNIDAD_CHOICES, default='unid')
    stock_global = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Material / Insumo'
        verbose_name_plural = 'Materiales / Insumos'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return self.nombre

    @property
    def bajo_stock_global(self):
        return self.stock_global <= self.stock_minimo


# ---------------------------------------------------------------------------
# ENTIDADES PRINCIPALES
# ---------------------------------------------------------------------------

class Trabajador(models.Model):
    TIPO_IDENTIFICACION_CHOICES = [
        ('RUT',       'RUT Chileno'),
        ('PASAPORTE', 'Pasaporte'),
        ('DNI',       'DNI / Cédula Extranjera'),
    ]
    ESTADO_CIVIL_CHOICES = [
        ('', '---------'),
        ('Soltero/a', 'Soltero/a'),
        ('Casado/a', 'Casado/a'),
        ('Conviviente Civil', 'Conviviente Civil'),
        ('Divorciado/a', 'Divorciado/a'),
        ('Viudo/a', 'Viudo/a'),
    ]
    rut = models.CharField(max_length=20, primary_key=True)
    tipo_identificacion = models.CharField(max_length=10, choices=TIPO_IDENTIFICACION_CHOICES, default='RUT')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(max_length=100, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    estado_civil = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES, blank=True, default='')
    nacionalidad = models.CharField(max_length=50, blank=True, default='Chilena')
    procedencia = models.CharField(max_length=100, blank=True)
    prevision = models.CharField(max_length=100, blank=True, help_text='AFP o INP')
    salud = models.CharField(max_length=100, blank=True, help_text='FONASA o Isapre')
    foto = models.ImageField(upload_to='fotos_trabajadores/', null=True, blank=True)
    en_lista_negra = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)
    creado_el = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.rut})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def strikes_activos(self):
        return self.strikes.filter(activo=True).count()

    @property
    def contratos_vigentes(self):
        return self.contratos.filter(estado='Vigente', activo=True)


class Obra(models.Model):
    ESTADO_CHOICES = [('Activa', 'Activa'), ('Pausada', 'Pausada'), ('Cerrada', 'Cerrada')]
    empresa = models.ForeignKey(
        'ConfigEmpresa',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='obras',
        verbose_name='Empresa Contratista',
    )
    nombre = models.CharField(max_length=150)
    constructora_mandante = models.CharField(max_length=150, blank=True)
    direccion = models.CharField(max_length=300, blank=True, verbose_name='Dirección / Ubicación de la Obra')
    monto_proyecto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_termino_estimada = models.DateField()
    fecha_termino_real = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activa')
    observaciones = models.TextField(blank=True)
    archivada = models.BooleanField(default=False)
    creado_el = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Obra'
        verbose_name_plural = 'Obras'
        ordering = ['-creado_el']

    def __str__(self):
        return self.nombre

    @property
    def contratos_vigentes_count(self):
        return self.contratos.filter(estado='Vigente', activo=True).count()

    @property
    def dotacion_activa(self):
        return self.contratos.filter(estado='Vigente', activo=True).select_related('trabajador', 'especialidad')


class Contrato(models.Model):
    ESTADO_CHOICES = [
        ('Borrador', 'Borrador'),
        ('Pendiente de Firma', 'Pendiente de Firma'),
        ('Vigente', 'Vigente'),
        ('En Licencia', 'En Licencia'),
        ('Reactivado', 'Reactivado'),
        ('Finalizado', 'Finalizado'),
        ('Finiquitado', 'Finiquitado'),
        ('Rescindido', 'Rescindido'),
        ('Trasladado', 'Trasladado'),
    ]
    TIPO_CONTRATO_CHOICES = [
        ('Plazo Fijo', 'Plazo Fijo'),
        ('Por Obra o Faena', 'Por Obra o Faena'),
        ('Indefinido', 'Indefinido'),
    ]
    TIPO_TERMINO_CHOICES = [
        ('', '— Sin término —'),
        ('Renuncia voluntaria', 'Renuncia voluntaria'),
        ('Despido por necesidades de la empresa', 'Despido por necesidades de la empresa'),
        ('Despido por incumplimiento grave', 'Despido por incumplimiento grave'),
        ('Mutuo acuerdo', 'Mutuo acuerdo'),
        ('Vencimiento plazo', 'Vencimiento plazo'),
        ('Término de obra o faena', 'Término de obra o faena'),
        ('Fallecimiento', 'Fallecimiento'),
        ('Invalidez', 'Invalidez'),
        ('Otro', 'Otro'),
    ]
    trabajador = models.ForeignKey(Trabajador, on_delete=models.PROTECT, related_name='contratos', to_field='rut')
    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='contratos')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT, related_name='contratos', null=True, blank=True)
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES, default='Plazo Fijo')
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_termino_estimada = models.DateField(null=True, blank=True)
    fecha_termino_real = models.DateField(null=True, blank=True)
    tipo_termino = models.CharField(max_length=60, blank=True, default='', choices=TIPO_TERMINO_CHOICES)
    motivo_termino = models.TextField(blank=True, default='')
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='Pendiente de Firma')
    fecha_inicio_licencia = models.DateField(null=True, blank=True)
    fecha_fin_licencia = models.DateField(null=True, blank=True)
    obs_licencia = models.TextField(blank=True, default='')
    creado_el = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)
    es_recontratacion = models.BooleanField(default=False)
    contrato_anterior = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='recontrataciones',
    )
    fecha_extension = models.DateField(
        null=True, blank=True,
        help_text='Fecha extendida por Anexo de Contrato. No modifica la fecha original.',
    )

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-creado_el']

    def __str__(self):
        return f"Contrato #{self.pk} - {self.trabajador.nombre_completo} | {self.obra.nombre}"

    _ESTADOS_TERMINADOS = {'Finalizado', 'Finiquitado', 'Rescindido', 'Trasladado'}

    @property
    def is_terminado(self):
        return self.estado in self._ESTADOS_TERMINADOS

    @property
    def fecha_vigencia_efectiva(self):
        return self.fecha_extension or self.fecha_termino_estimada

    @property
    def dias_para_vencer(self):
        fecha = self.fecha_vigencia_efectiva
        if fecha:
            return (fecha - timezone.now().date()).days
        return None


# ---------------------------------------------------------------------------
# DOCUMENTOS
# ---------------------------------------------------------------------------

class Documento(models.Model):
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, related_name='documentos')
    trabajador_rut = models.CharField(max_length=12, blank=True, null=True)
    trabajador_nombre = models.CharField(max_length=200, blank=True, null=True)
    contrato = models.ForeignKey(Contrato, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos')
    obra = models.ForeignKey(Obra, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos')
    archivo = models.FileField(upload_to=documento_upload_path, null=True, blank=True)
    fecha_carga = models.DateTimeField(default=timezone.now)
    # Fecha de vencimiento: calculada automáticamente si el tipo tiene dias_validez,
    # pero también puede ajustarse manualmente (ej. certificados con fecha impresa).
    fecha_vencimiento = models.DateField(null=True, blank=True)
    usuario_carga = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    pendiente_digitalizacion = models.BooleanField(
        default=False,
        help_text='El papel existe pero aún no se ha escaneado/subido el archivo.'
    )

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-fecha_carga']

    def save(self, *args, **kwargs):
        # Auto-calcular fecha_vencimiento si el tipo tiene dias_validez y no se definió manualmente
        if not self.fecha_vencimiento and self.tipo_documento_id:
            try:
                tipo = self.tipo_documento if hasattr(self, '_tipo_documento_cache') else TipoDocumento.objects.get(pk=self.tipo_documento_id)
                if tipo.dias_validez:
                    from datetime import timedelta
                    base = self.fecha_carga.date() if self.fecha_carga else timezone.now().date()
                    self.fecha_vencimiento = base + timedelta(days=tipo.dias_validez)
            except TipoDocumento.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        ref = self.trabajador_rut or f"Obra {self.obra_id}"
        return f"{self.tipo_documento.nombre} - {ref}"

    @property
    def nombre_archivo(self):
        if not self.archivo:
            return ''
        return os.path.basename(self.archivo.name)

    @property
    def extension(self):
        if self.archivo:
            return self.archivo.name.split('.')[-1].upper()
        return ''

    @property
    def esta_vencido(self):
        if self.fecha_vencimiento:
            return timezone.now().date() > self.fecha_vencimiento
        return False

    @property
    def dias_para_vencer(self):
        if self.fecha_vencimiento:
            return (self.fecha_vencimiento - timezone.now().date()).days
        return None

    @property
    def estado_visual(self):
        """Retorna: 'ok', 'vencido', 'proximo', 'pendiente_dig'."""
        if self.pendiente_digitalizacion and not self.archivo:
            return 'pendiente_dig'
        if self.esta_vencido:
            return 'vencido'
        if self.dias_para_vencer is not None and self.dias_para_vencer <= 30:
            return 'proximo'
        return 'ok'


# ---------------------------------------------------------------------------
# STRIKES Y LISTA NEGRA
# ---------------------------------------------------------------------------

class Strike(models.Model):
    CATEGORIA_CHOICES = [
        ('Drogas', 'Drogas'), ('Alcohol', 'Alcohol'), ('Pelea', 'Pelea'),
        ('Robo', 'Robo'), ('Ausencia', 'Ausencia'), ('Mala conducta', 'Mala conducta'),
        ('Otro', 'Otro'),
    ]
    trabajador = models.ForeignKey(Trabajador, on_delete=models.PROTECT, related_name='strikes', to_field='rut')
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    descripcion = models.TextField()
    fecha_incidente = models.DateField()
    creado_el = models.DateTimeField(default=timezone.now)
    usuario_registro = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Strike'
        verbose_name_plural = 'Strikes'
        ordering = ['-fecha_incidente']

    def __str__(self):
        return f"Strike {self.categoria} - {self.trabajador.nombre_completo} ({self.fecha_incidente})"


class HistorialListaNegra(models.Model):
    ACCION_CHOICES = [('INGRESO', 'Ingreso a Lista Negra'), ('SALIDA', 'Salida de Lista Negra')]
    trabajador = models.ForeignKey(Trabajador, on_delete=models.PROTECT, related_name='historial_lista_negra', to_field='rut')
    accion = models.CharField(max_length=10, choices=ACCION_CHOICES)
    motivo = models.TextField()
    fecha_registro = models.DateTimeField(default=timezone.now)
    usuario_registro = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Historial Lista Negra'
        verbose_name_plural = 'Historial Lista Negra'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.accion} - {self.trabajador.nombre_completo} ({self.fecha_registro.date()})"


# ---------------------------------------------------------------------------
# BODEGA / MATERIALES
# ---------------------------------------------------------------------------

class BodegaObra(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='bodega_items')
    material = models.ForeignKey(CatalogoMaterial, on_delete=models.PROTECT, related_name='bodega_items')
    stock_actual = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Bodega Obra'
        verbose_name_plural = 'Bodega Obras'
        unique_together = [('obra', 'material')]

    def __str__(self):
        return f"{self.material.nombre} en {self.obra.nombre}: {self.stock_actual}"

    @property
    def bajo_stock(self):
        return self.stock_actual < self.material.stock_minimo


class HistorialMaterial(models.Model):
    TIPO_CHOICES = [
        ('INGRESO_STOCK', 'Ingreso de Stock'),
        ('ENTREGA_TERRENO', 'Entrega en Terreno'),
        ('AJUSTE', 'Ajuste de Inventario'),
    ]
    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='historial_materiales', null=True, blank=True)
    material = models.ForeignKey(CatalogoMaterial, on_delete=models.PROTECT, related_name='historial')
    trabajador_capataz = models.ForeignKey(Trabajador, on_delete=models.PROTECT, related_name='despachos_recibidos',
                                           to_field='rut', null=True, blank=True)
    receptor_libre = models.CharField(max_length=150, blank=True, default='')
    cantidad = models.IntegerField()
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_CHOICES)
    observacion = models.TextField(blank=True)
    fecha_movimiento = models.DateTimeField(default=timezone.now)
    usuario_registro = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Movimiento de Material'
        verbose_name_plural = 'Movimientos de Materiales'
        ordering = ['-fecha_movimiento']

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.material.nombre} x{self.cantidad} ({self.fecha_movimiento.date()})"


# ---------------------------------------------------------------------------
# CIERRES MENSUALES
# ---------------------------------------------------------------------------

class CierreMensual(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='cierres_mensuales')
    mes = models.IntegerField()
    anio = models.IntegerField()
    descripcion = models.CharField(max_length=120, blank=True, default='')
    fecha_cierre = models.DateTimeField(default=timezone.now)
    usuario_cierre = models.CharField(max_length=100)
    archivo_consolidado = models.FileField(upload_to=cierre_upload_path, null=True, blank=True)

    class Meta:
        verbose_name = 'Cierre Mensual'
        verbose_name_plural = 'Cierres Mensuales'
        ordering = ['-anio', '-mes', '-fecha_cierre']
        unique_together = [('obra', 'mes', 'anio')]

    def __str__(self):
        return f"Cierre {self.mes}/{self.anio} - {self.obra.nombre}"


# ---------------------------------------------------------------------------
# AUDITORÍA
# ---------------------------------------------------------------------------

class LogAuditoria(models.Model):
    fecha_hora = models.DateTimeField(default=timezone.now)
    usuario = models.CharField(max_length=100)
    accion = models.CharField(max_length=50)
    tabla_afectada = models.CharField(max_length=50)
    registro_id = models.CharField(max_length=50)
    detalle_cambio = models.JSONField()

    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.accion} en {self.tabla_afectada} #{self.registro_id} por {self.usuario}"


# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE EMPRESA
# ---------------------------------------------------------------------------

class ConfigEmpresa(models.Model):
    nombre = models.CharField(max_length=200)
    rut_empresa = models.CharField(max_length=20)
    giro = models.CharField(max_length=100, blank=True, default='Constructora')
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    correo_electronico = models.EmailField(max_length=150, blank=True)
    nombre_representante = models.CharField(max_length=150)
    rut_representante = models.CharField(max_length=20)
    cargo_representante = models.CharField(max_length=100, blank=True, default='Representante Legal')
    activo = models.BooleanField(default=True)
    creado_el = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rut_empresa})"


# ---------------------------------------------------------------------------
# DOCUMENTOS GENERADOS (plantillas llenadas digitalmente)
# ---------------------------------------------------------------------------

class DocumentoGenerado(models.Model):
    TIPO_CHOICES = [
        ('contrato_trabajo', 'Contrato de Trabajo'),
        ('anexo_contrato', 'Anexo Contrato de Trabajo'),
        ('finiquito', 'Finiquito de Trabajo'),
        ('pacto_horas_extras', 'Pacto Horas Extraordinarias'),
        ('acta_epp', 'Acta Entrega EPP'),
        ('acta_reglamento', 'Acta Entrega Reglamento Interno'),
        ('acta_reactivacion', 'Acta de Reactivación Post-Licencia'),
    ]
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    empresa = models.ForeignKey(ConfigEmpresa, on_delete=models.PROTECT, related_name='documentos_generados')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.PROTECT, related_name='documentos_generados', to_field='rut')
    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='documentos_generados', null=True, blank=True)
    contrato = models.ForeignKey('Contrato', on_delete=models.PROTECT, related_name='documentos_generados', null=True, blank=True)
    datos = models.JSONField(default=dict)
    motivo_baja = models.TextField(
        blank=True, default='',
        help_text='Motivo por el cual se reemplazó o anuló este documento (trazabilidad de auditoría).'
    )
    creado_el = models.DateTimeField(default=timezone.now)
    usuario = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Documento Generado'
        verbose_name_plural = 'Documentos Generados'
        ordering = ['-creado_el']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.trabajador.nombre_completo}"


# ---------------------------------------------------------------------------
# UTILIDAD: Checklist de documentos (cálculo en vivo, no tabla)
# ---------------------------------------------------------------------------

def get_checklist_trabajador(rut):
    """
    Devuelve el checklist de documentos del nivel Trabajador para un RUT.
    Retorna una lista de dicts con: tipo, doc (último activo o None), docs_historial (todos activos),
    estado ('ok'|'vencido'|'proximo'|'pendiente'|'pendiente_dig').
    """
    tipos = TipoDocumento.objects.filter(activo=True, nivel='Trabajador')
    resultado = []
    for tipo in tipos:
        docs_all = list(
            Documento.objects
            .filter(tipo_documento=tipo, trabajador_rut=rut, activo=True)
            .order_by('-fecha_carga')
        )
        doc = docs_all[0] if docs_all else None
        if doc is None:
            estado = 'pendiente'
        elif doc.pendiente_digitalizacion and not doc.archivo:
            estado = 'pendiente_dig'
        elif doc.esta_vencido:
            estado = 'vencido'
        elif doc.dias_para_vencer is not None and doc.dias_para_vencer <= 30:
            estado = 'proximo'
        else:
            estado = 'ok'
        resultado.append({'tipo': tipo, 'doc': doc, 'docs_historial': docs_all, 'estado': estado})
    return resultado


def get_checklist_contrato(contrato):
    """
    Devuelve el checklist de documentos del nivel Contrato para un contrato dado.
    Retorna lista de dicts con: tipo, doc, docs_historial, estado.
    """
    tipos = TipoDocumento.objects.filter(activo=True, nivel='Contrato')
    resultado = []
    for tipo in tipos:
        docs_all = list(
            Documento.objects
            .filter(tipo_documento=tipo, contrato=contrato, activo=True)
            .order_by('-fecha_carga')
        )
        doc = docs_all[0] if docs_all else None
        if doc is None:
            estado = 'pendiente'
        elif doc.pendiente_digitalizacion and not doc.archivo:
            estado = 'pendiente_dig'
        elif doc.esta_vencido:
            estado = 'vencido'
        else:
            estado = 'ok'
        resultado.append({'tipo': tipo, 'doc': doc, 'docs_historial': docs_all, 'estado': estado})
    return resultado


# ---------------------------------------------------------------------------
# TRASLADOS DE PERSONAL
# ---------------------------------------------------------------------------

class Traslado(models.Model):
    TIPO_CHOICES = [
        ('SIN_FINIQUITO', 'Traslado sin Finiquito (Contrato Continúa)'),
        ('CON_FINIQUITO', 'Traslado con Finiquito (Nuevo Contrato)'),
    ]
    trabajador = models.ForeignKey(Trabajador, on_delete=models.PROTECT, related_name='traslados', to_field='rut')
    contrato_origen = models.ForeignKey(
        'Contrato', on_delete=models.PROTECT, related_name='traslado_como_origen', null=True, blank=True
    )
    obra_origen = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='traslados_salida')
    obra_destino = models.ForeignKey(
        Obra, on_delete=models.PROTECT, related_name='traslados_entrada', null=True, blank=True
    )
    contrato_destino = models.ForeignKey(
        'Contrato', on_delete=models.PROTECT, related_name='traslado_como_destino', null=True, blank=True
    )
    tipo_traslado = models.CharField(max_length=20, choices=TIPO_CHOICES)
    finiquito_pendiente = models.BooleanField(default=False)
    fecha_traslado = models.DateField()
    observaciones = models.TextField(blank=True)
    usuario_registro = models.CharField(max_length=150)
    creado_el = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Traslado'
        verbose_name_plural = 'Traslados'
        ordering = ['-creado_el']

    def __str__(self):
        return f"Traslado {self.trabajador.nombre_completo}: {self.obra_origen} → {self.obra_destino or 'Pendiente'}"

    @property
    def requiere_finiquito(self):
        return self.tipo_traslado == 'CON_FINIQUITO' and self.finiquito_pendiente


# ---------------------------------------------------------------------------
# LICENCIAS MÉDICAS
# ---------------------------------------------------------------------------

def licencia_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    rut = re.sub(r'[^\w\-]', '_', str(instance.trabajador_id or 'sin_rut'))
    return os.path.join('documentos', 'trabajadores', rut, 'licencias', f'LIC_{ts}.{ext}')


class LicenciaMedica(models.Model):
    TIPO_CHOICES = [
        ('1', 'Tipo 1 — Enfermedad o accidente común'),
        ('2', 'Tipo 2 — Accidente laboral / enfermedad profesional (ACHS/Mutual)'),
        ('3', 'Tipo 3 — Prenatal'),
        ('4', 'Tipo 4 — Postnatal / hijo menor 1 año'),
        ('5', 'Tipo 5 — Accidente trabajo de otro trabajador'),
        ('6', 'Tipo 6 — Enfermedad terminal / desahucio'),
        ('7', 'Tipo 7 — Ley SANNA (hijo hasta 18 años)'),
        ('otro', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('Presentada', 'Presentada'),
        ('En trámite', 'En trámite'),
        ('Autorizada', 'Autorizada'),
        ('Rechazada', 'Rechazada'),
        ('Prorrogada', 'Prorrogada'),
    ]
    ORGANISMO_CHOICES = [
        ('FONASA', 'FONASA'),
        ('ISAPRE', 'ISAPRE'),
        ('ACHS', 'ACHS'),
        ('Mutual de Seguridad', 'Mutual de Seguridad'),
        ('IST', 'IST'),
        ('Otro', 'Otro'),
    ]
    contrato = models.ForeignKey(
        Contrato, on_delete=models.PROTECT, related_name='licencias', null=True, blank=True
    )
    trabajador = models.ForeignKey(
        Trabajador, on_delete=models.PROTECT, related_name='licencias', to_field='rut'
    )
    obra = models.ForeignKey(
        Obra, on_delete=models.PROTECT, related_name='licencias', null=True, blank=True
    )
    numero_folio = models.CharField(max_length=50, blank=True, default='')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='1')
    organismo = models.CharField(max_length=30, choices=ORGANISMO_CHOICES, default='FONASA')
    institucion_nombre = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Hospital, clínica, mutual o mutualidad que emitió la licencia. Ej: Mutual de Seguridad, Hospital Las Higueras.'
    )
    diagnostico = models.TextField(blank=True, default='')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    dias_autorizados = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Presentada')
    empresa_pago_3_dias = models.BooleanField(
        default=False,
        help_text='Para tipo 1: ¿la empresa pagó los 3 primeros días?'
    )
    monto_subsidio_esperado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monto_subsidio_recibido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    archivo_formulario = models.FileField(upload_to=licencia_upload_path, null=True, blank=True)
    archivo_resolucion = models.FileField(upload_to=licencia_upload_path, null=True, blank=True)
    archivo_alta = models.FileField(upload_to=licencia_upload_path, null=True, blank=True)
    observaciones = models.TextField(blank=True, default='')
    usuario_registro = models.CharField(max_length=150)
    creado_el = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Licencia Médica'
        verbose_name_plural = 'Licencias Médicas'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Lic. {self.get_tipo_display()} — {self.trabajador.nombre_completo} ({self.fecha_inicio})"

    @property
    def dias_efectivos(self):
        if self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days + 1
        return self.dias_autorizados or 0

    @property
    def esta_activa(self):
        from django.utils import timezone as tz
        hoy = tz.now().date()
        if not self.activo:
            return False
        if self.fecha_fin:
            return self.fecha_inicio <= hoy <= self.fecha_fin
        return self.fecha_inicio <= hoy

    @property
    def dias_transcurridos(self):
        from django.utils import timezone as tz
        hoy = tz.now().date()
        if self.fecha_inicio > hoy:
            return 0
        fin = min(self.fecha_fin, hoy) if self.fecha_fin else hoy
        return (fin - self.fecha_inicio).days + 1


# ---------------------------------------------------------------------------
# HISTORIAL DE ESTADOS DE CONTRATO (audit log)
# ---------------------------------------------------------------------------

class ContratoHistorial(models.Model):
    contrato = models.ForeignKey(
        Contrato, on_delete=models.CASCADE, related_name='historial'
    )
    estado_anterior = models.CharField(max_length=30)
    estado_nuevo = models.CharField(max_length=30)
    descripcion = models.TextField(blank=True, default='')
    usuario = models.CharField(max_length=150)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Historial Contrato'
        verbose_name_plural = 'Historial Contratos'
        ordering = ['-fecha']

    def __str__(self):
        return f"Contrato #{self.contrato_id}: {self.estado_anterior} → {self.estado_nuevo}"


# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE REMUNERACIONES (tasas AFP/Salud)
# ---------------------------------------------------------------------------

class ConfigRemuneraciones(models.Model):
    AFP_CHOICES = [
        ('Capital', 'Capital'),
        ('Cuprum', 'Cuprum'),
        ('Habitat', 'Hábitat'),
        ('PlanVital', 'PlanVital'),
        ('ProVida', 'ProVida'),
        ('Modelo', 'Modelo'),
        ('Uno', 'Uno'),
        ('IPS/INP', 'IPS/INP (antiguo)'),
    ]
    nombre = models.CharField(max_length=100, default='Configuración General')
    vigente_desde = models.DateField()
    tasa_afp_empleado = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.58,
        help_text='% cotización obligatoria AFP (varía por AFP)'
    )
    tasa_salud_empleado = models.DecimalField(
        max_digits=5, decimal_places=2, default=7.00,
        help_text='% cotización salud obligatoria'
    )
    tasa_cesantia_empleado_plazo_fijo = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.60,
        help_text='% seguro cesantía empleado (plazo fijo)'
    )
    tasa_cesantia_empleado_indefinido = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.60,
        help_text='% seguro cesantía empleado (indefinido)'
    )
    tasa_cesantia_empleador = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.40,
        help_text='% seguro cesantía empleador'
    )
    tasa_mutual_accidentes = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.93,
        help_text='% seguro accidentes del trabajo (varía por empresa)'
    )
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Config. Remuneraciones'
        verbose_name_plural = 'Config. Remuneraciones'
        ordering = ['-vigente_desde']

    def __str__(self):
        return f"{self.nombre} (desde {self.vigente_desde})"

    @classmethod
    def vigente(cls):
        from django.utils import timezone as tz
        return cls.objects.filter(activo=True, vigente_desde__lte=tz.now().date()).first()


def get_alertas_cruzadas(rut):
    """
    Retorna alertas de traslados pendientes: finiquitos faltantes en obras anteriores.
    Devuelve lista de dicts con: tipo, traslado, obra, mensaje
    """
    alertas = []
    traslados = Traslado.objects.filter(
        trabajador_id=rut,
        tipo_traslado='CON_FINIQUITO',
        finiquito_pendiente=True,
        activo=True
    ).select_related('obra_origen', 'contrato_origen', 'obra_destino')

    for t in traslados:
        if t.contrato_origen:
            tiene_finiquito = Documento.objects.filter(
                contrato=t.contrato_origen,
                tipo_documento__nombre__icontains='finiquito',
                activo=True
            ).exists()
            if tiene_finiquito:
                t.finiquito_pendiente = False
                t.save(update_fields=['finiquito_pendiente'])
                continue
        alertas.append({
            'tipo': 'FINIQUITO_PENDIENTE',
            'traslado': t,
            'obra': t.obra_origen,
            'mensaje': f'Falta el finiquito en la obra "{t.obra_origen.nombre}"',
        })
    return alertas
