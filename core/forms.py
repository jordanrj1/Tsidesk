from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Trabajador, Obra, Contrato, Documento, Strike,
    HistorialListaNegra, BodegaObra, HistorialMaterial,
    CierreMensual, TipoDocumento, Especialidad, CatalogoMaterial,
    ConfigEmpresa
)


# ---------------------------------------------------------------------------
# VALIDACIÓN RUT MÓDULO 11
# ---------------------------------------------------------------------------

def validar_rut_modulo11(rut):
    """Valida RUT chileno con algoritmo Módulo 11. Retorna True si es válido."""
    import re
    rut_clean = re.sub(r'[\.\-\s]', '', str(rut)).upper()
    if len(rut_clean) < 2:
        return False
    cuerpo = rut_clean[:-1]
    dv = rut_clean[-1]
    if not cuerpo.isdigit():
        return False
    suma, multiplo = 0, 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    resto = 11 - (suma % 11)
    dv_calc = '0' if resto == 11 else 'K' if resto == 10 else str(resto)
    return dv == dv_calc


# ---------------------------------------------------------------------------
# TRABAJADOR
# ---------------------------------------------------------------------------

_OBS_PLACEHOLDER = (
    "Ejemplos de lo que se puede registrar aquí:\n"
    "• Restricciones médicas o físicas (ej: no puede trabajar en altura)\n"
    "• Certificaciones o licencias especiales (ej: licencia clase B vigente)\n"
    "• Antecedentes de traslado o préstamo a otras obras\n"
    "• Contacto de emergencia (nombre y teléfono)\n"
    "• Motivo de ingreso o referencia (ej: recomendado por capataz Juan Pérez)\n"
    "• Observaciones del proceso de contratación"
)

class TrabajadorForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = Trabajador
        fields = ['tipo_identificacion', 'rut', 'nombres', 'apellidos', 'telefono', 'correo',
                  'direccion', 'ciudad', 'fecha_nacimiento',
                  'nacionalidad', 'estado_civil', 'procedencia', 'prevision', 'salud',
                  'foto', 'observaciones']
        widgets = {
            'tipo_identificacion': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_identificacion'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9', 'id': 'id_rut'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +56 9 8765 4321'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: nombre@gmail.com'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Los Carrera 1234, Concepción'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Concepción'}),
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': _OBS_PLACEHOLDER}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telefono'].required = True
        self.fields['correo'].required = True
        self.fields['ciudad'].required = True
        self.fields['direccion'].required = True
        # Datos previsionales — dropdowns con listas definidas más abajo en este módulo
        self.fields['nacionalidad'].widget = forms.Select(choices=_NACIONALIDAD_CHOICES, attrs={'class': 'form-select'})
        self.fields['nacionalidad'].required = False
        self.fields['estado_civil'].widget = forms.Select(choices=_ESTADO_CIVIL_CHOICES, attrs={'class': 'form-select'})
        self.fields['estado_civil'].required = False
        self.fields['procedencia'].widget = forms.Select(choices=_CIUDAD_CHOICES, attrs={'class': 'form-select'})
        self.fields['procedencia'].required = False
        self.fields['prevision'].widget = forms.Select(choices=_AFP_CHOICES, attrs={'class': 'form-select'})
        self.fields['prevision'].required = False
        self.fields['salud'].widget = forms.Select(choices=_SALUD_CHOICES, attrs={'class': 'form-select'})
        self.fields['salud'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_identificacion', 'RUT')
        rut = cleaned_data.get('rut', '')
        if tipo == 'RUT':
            import re
            rut_clean = re.sub(r'[\.\-\s]', '', str(rut)).upper()
            # Only validate format: digits + optional K as last char, min 7 chars total
            if not re.match(r'^\d{6,8}[0-9Kk]$', rut_clean):
                self.add_error('rut', 'Formato de RUT inválido. Use: 12.345.678-9 o 12345678-K')
        else:
            import re
            clean_id = re.sub(r'[\s\-\.]', '', rut)
            if len(clean_id) < 4 or not re.match(r'^[A-Za-z0-9]+$', clean_id):
                self.add_error('rut', 'Número de documento inválido. Use solo letras y números (mínimo 4 caracteres).')
        return cleaned_data


class TrabajadorEditForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = Trabajador
        fields = ['nombres', 'apellidos', 'telefono', 'correo', 'direccion', 'ciudad',
                  'fecha_nacimiento', 'nacionalidad', 'estado_civil', 'procedencia',
                  'prevision', 'salud', 'foto', 'observaciones']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Los Carrera 1234, Concepción'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Concepción'}),
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _OBS_PLACEHOLDER}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nacionalidad'].widget = forms.Select(choices=_NACIONALIDAD_CHOICES, attrs={'class': 'form-select'})
        self.fields['nacionalidad'].required = False
        self.fields['estado_civil'].widget = forms.Select(choices=_ESTADO_CIVIL_CHOICES, attrs={'class': 'form-select'})
        self.fields['estado_civil'].required = False
        self.fields['procedencia'].widget = forms.Select(choices=_CIUDAD_CHOICES, attrs={'class': 'form-select'})
        self.fields['procedencia'].required = False
        self.fields['prevision'].widget = forms.Select(choices=_AFP_CHOICES, attrs={'class': 'form-select'})
        self.fields['prevision'].required = False
        self.fields['salud'].widget = forms.Select(choices=_SALUD_CHOICES, attrs={'class': 'form-select'})
        self.fields['salud'].required = False


# ---------------------------------------------------------------------------
# OBRA
# ---------------------------------------------------------------------------

class ObraForm(forms.ModelForm):
    fecha_inicio = forms.DateField(
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa'}),
    )
    fecha_termino_estimada = forms.DateField(
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa'}),
    )
    fecha_termino_real = forms.DateField(
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa (opcional)'}),
        required=False,
    )

    class Meta:
        model = Obra
        fields = ['nombre', 'empresa', 'constructora_mandante', 'direccion', 'monto_proyecto',
                  'fecha_inicio', 'fecha_termino_estimada', 'fecha_termino_real',
                  'estado', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Edificio Los Pinos — Etapa 2'}),
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'constructora_mandante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Constructora Socobec SpA'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Av. Los Carrera 1234, Concepción'}),
            'monto_proyecto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import ConfigEmpresa
        self.fields['empresa'].queryset = ConfigEmpresa.objects.filter(activo=True)
        self.fields['empresa'].empty_label = '--- Seleccionar empresa ---'
        self.fields['empresa'].required = False


# ---------------------------------------------------------------------------
# CONTRATO
# ---------------------------------------------------------------------------

class ContratoForm(forms.ModelForm):
    fecha_inicio = forms.DateField(
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa'}),
    )
    fecha_termino_estimada = forms.DateField(
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa (opcional)'}),
        required=False,
    )

    class Meta:
        model = Contrato
        # 'estado' excluded — always defaults to 'Pendiente de Firma' on creation
        fields = ['trabajador', 'obra', 'especialidad', 'tipo_contrato', 'sueldo_base',
                  'fecha_inicio', 'fecha_termino_estimada']
        widgets = {
            'trabajador': forms.Select(attrs={'class': 'form-select'}),
            'obra': forms.Select(attrs={'class': 'form-select'}),
            'especialidad': forms.Select(attrs={'class': 'form-select'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'sueldo_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        trabajador_rut = kwargs.pop('trabajador_rut', None)
        obra_id = kwargs.pop('obra_id', None)
        super().__init__(*args, **kwargs)
        from .models import Trabajador, Obra, Especialidad
        self.fields['trabajador'].queryset = Trabajador.objects.filter(activo=True, en_lista_negra=False)
        self.fields['obra'].queryset = Obra.objects.filter(activo=True, estado__in=['Activa', 'Pausada'])
        self.fields['especialidad'].queryset = Especialidad.objects.filter(activo=True)
        if trabajador_rut:
            try:
                t = Trabajador.objects.get(rut=trabajador_rut)
                self.fields['trabajador'].initial = t
                self.fields['trabajador'].widget.attrs['readonly'] = True
            except Trabajador.DoesNotExist:
                pass
        if obra_id:
            try:
                o = Obra.objects.get(pk=obra_id)
                self.fields['obra'].initial = o
            except Obra.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_termino = cleaned_data.get('fecha_termino_estimada')
        if fecha_inicio and fecha_termino and fecha_termino < fecha_inicio:
            self.add_error('fecha_termino_estimada',
                           "La fecha de término debe ser posterior a la fecha de inicio.")
        return cleaned_data


class ContratoEditForm(forms.ModelForm):
    fecha_termino_estimada = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    fecha_termino_real = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)

    class Meta:
        model = Contrato
        fields = ['tipo_contrato', 'sueldo_base', 'fecha_termino_estimada', 'fecha_termino_real', 'estado']
        widgets = {
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'sueldo_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }


# ---------------------------------------------------------------------------
# DOCUMENTO
# ---------------------------------------------------------------------------

class DocumentoForm(forms.ModelForm):
    fecha_vencimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Se calcula automáticamente según el tipo. Solo ajustar si la fecha impresa en el documento difiere.',
    )

    class Meta:
        model = Documento
        fields = ['tipo_documento', 'archivo', 'fecha_vencimiento']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }

    def __init__(self, *args, nivel=None, **kwargs):
        super().__init__(*args, **kwargs)
        if nivel:
            self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True, nivel=nivel)
        else:
            self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True)

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            if archivo.size == 0:
                raise forms.ValidationError('El archivo está vacío. Seleccione un archivo válido.')
            if archivo.size > 20 * 1024 * 1024:  # 20MB
                raise forms.ValidationError('El archivo supera el límite de 20MB.')
        return archivo


# ---------------------------------------------------------------------------
# STRIKES
# ---------------------------------------------------------------------------

class StrikeForm(forms.ModelForm):
    fecha_incidente = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model = Strike
        fields = ['categoria', 'descripcion', 'fecha_incidente']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StrikeEditForm(forms.ModelForm):
    fecha_incidente = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model = Strike
        fields = ['categoria', 'descripcion', 'fecha_incidente']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


# ---------------------------------------------------------------------------
# LISTA NEGRA
# ---------------------------------------------------------------------------

class ListaNegraIngresoForm(forms.Form):
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'minlength': '20'}),
        min_length=20,
        label='Motivo del veto (mínimo 20 caracteres)',
    )


class ListaNegraSalidaForm(forms.Form):
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'minlength': '20'}),
        min_length=20,
        label='Justificación de amnistía (mínimo 20 caracteres)',
    )


# ---------------------------------------------------------------------------
# BODEGA
# ---------------------------------------------------------------------------

class DespachoMaterialForm(forms.Form):
    obra_id = forms.IntegerField(widget=forms.HiddenInput())
    material_id = forms.IntegerField(widget=forms.HiddenInput())
    capataz_rut = forms.ChoiceField(label='Capataz receptor', widget=forms.Select(attrs={'class': 'form-select'}))
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    observacion = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    def __init__(self, obra=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if obra:
            from .models import Contrato, Especialidad
            capataz_esp = Especialidad.objects.filter(nombre__icontains='capataz').first()
            qs = Contrato.objects.filter(obra=obra, estado='Vigente', activo=True).select_related('trabajador')
            choices = [('', '--- Seleccione capataz ---')]
            for c in qs:
                choices.append((c.trabajador.rut, f"{c.trabajador.nombre_completo} ({c.trabajador.rut})"))
            self.fields['capataz_rut'].choices = choices


class IngresoStockForm(forms.Form):
    obra_id = forms.IntegerField(widget=forms.HiddenInput())
    material_id = forms.IntegerField(widget=forms.HiddenInput())
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    observacion = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class AjusteUmbralForm(forms.ModelForm):
    class Meta:
        model = CatalogoMaterial
        fields = ['stock_minimo']
        widgets = {'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'})}


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN DE CATÁLOGOS
# ---------------------------------------------------------------------------

class TipoDocumentoForm(forms.ModelForm):
    class Meta:
        model = TipoDocumento
        fields = ['nombre', 'nivel', 'obligatorio', 'dias_validez', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'dias_validez': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 365 (dejar vacío = no vence)',
                'min': '1',
            }),
        }


class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ['nombre', 'activo']
        widgets = {'nombre': forms.TextInput(attrs={'class': 'form-control'})}


class CatalogoMaterialForm(forms.ModelForm):
    class Meta:
        model = CatalogoMaterial
        fields = ['nombre', 'stock_minimo', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ---------------------------------------------------------------------------
# USUARIOS (Super Admin)
# ---------------------------------------------------------------------------

class UsuarioCreateForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class UsuarioEditForm(forms.ModelForm):
    nueva_password = forms.CharField(
        label='Nueva contraseña (dejar en blanco para no cambiar)',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    is_superuser = forms.BooleanField(label='Es Super Admin', required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active', 'is_superuser']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        nueva_pw = self.cleaned_data.get('nueva_password')
        if nueva_pw:
            user.set_password(nueva_pw)
        if commit:
            user.save()
        return user


# ---------------------------------------------------------------------------
# CONFIGURACIÓN EMPRESA
# ---------------------------------------------------------------------------

class ConfigEmpresaForm(forms.ModelForm):
    class Meta:
        model = ConfigEmpresa
        fields = ['nombre', 'rut_empresa', 'giro', 'direccion', 'ciudad',
                  'correo_electronico', 'nombre_representante', 'rut_representante',
                  'cargo_representante', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Constructora San Joaquín SpA'}),
            'rut_empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 77.476.775-4'}),
            'giro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Construcción de edificaciones'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pasaje 3 1100 MZ I LT 8 Villa Los Aromos'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tomé'}),
            'correo_electronico': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.cl'}),
            'nombre_representante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Carlos García Montecinos'}),
            'rut_representante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 10.903.938-1'}),
            'cargo_representante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Representante Legal'}),
        }


# ---------------------------------------------------------------------------
# OPCIONES COMPARTIDAS PARA DOCUMENTOS GENERADOS
# ---------------------------------------------------------------------------

_CIUDAD_CHOICES = [
    ('', '--- Seleccionar ciudad ---'),
    ('Concepción', 'Concepción'),
    ('Talcahuano', 'Talcahuano'),
    ('Chiguayante', 'Chiguayante'),
    ('Hualpén', 'Hualpén'),
    ('San Pedro de la Paz', 'San Pedro de la Paz'),
    ('Coronel', 'Coronel'),
    ('Lota', 'Lota'),
    ('Hualqui', 'Hualqui'),
    ('Penco', 'Penco'),
    ('Tomé', 'Tomé'),
    ('Florida', 'Florida'),
    ('Santa Juana', 'Santa Juana'),
    ('Lebu', 'Lebu'),
    ('Cañete', 'Cañete'),
    ('Los Ángeles', 'Los Ángeles'),
    ('Chillán', 'Chillán'),
    ('Temuco', 'Temuco'),
    ('Valdivia', 'Valdivia'),
    ('Osorno', 'Osorno'),
    ('Puerto Montt', 'Puerto Montt'),
    ('Santiago', 'Santiago'),
    ('Valparaíso', 'Valparaíso'),
    ('Viña del Mar', 'Viña del Mar'),
    ('La Serena', 'La Serena'),
    ('Coquimbo', 'Coquimbo'),
    ('Antofagasta', 'Antofagasta'),
    ('Iquique', 'Iquique'),
    ('Arica', 'Arica'),
    ('Punta Arenas', 'Punta Arenas'),
    ('Otra', 'Otra (indicar en observaciones)'),
]

_ESTADO_CIVIL_CHOICES = [
    ('', '--- Seleccionar ---'),
    ('Soltero/a', 'Soltero/a'),
    ('Casado/a', 'Casado/a'),
    ('Conviviente Civil', 'Conviviente Civil'),
    ('Divorciado/a', 'Divorciado/a'),
    ('Viudo/a', 'Viudo/a'),
]

_AFP_CHOICES = [
    ('', '--- Seleccionar AFP ---'),
    ('AFP Habitat', 'AFP Habitat'),
    ('AFP Capital', 'AFP Capital'),
    ('AFP Cuprum', 'AFP Cuprum'),
    ('AFP Provida', 'AFP Provida (MetLife)'),
    ('AFP PlanVital', 'AFP PlanVital'),
    ('AFP Modelo', 'AFP Modelo'),
    ('AFP Uno', 'AFP Uno'),
    ('IPS / INP', 'IPS / INP (ex INP)'),
]

_SALUD_CHOICES = [
    ('', '--- Seleccionar ---'),
    ('FONASA', 'FONASA'),
    ('Isapre Banmédica', 'Isapre Banmédica'),
    ('Isapre Cruz Blanca', 'Isapre Cruz Blanca'),
    ('Isapre Colmena', 'Isapre Colmena'),
    ('Isapre MásVida', 'Isapre MásVida'),
    ('Isapre VidaTres', 'Isapre VidaTres'),
    ('Isapre Esencial', 'Isapre Esencial'),
]

_NACIONALIDAD_CHOICES = [
    ('', '--- Seleccionar ---'),
    ('Chilena', 'Chilena'),
    ('Venezolana', 'Venezolana'),
    ('Colombiana', 'Colombiana'),
    ('Peruana', 'Peruana'),
    ('Boliviana', 'Boliviana'),
    ('Ecuatoriana', 'Ecuatoriana'),
    ('Argentina', 'Argentina'),
    ('Haitiana', 'Haitiana'),
    ('Cubana', 'Cubana'),
    ('Dominicana', 'Dominicana'),
    ('Otra', 'Otra'),
]

_SEL = {'class': 'form-select'}
_INP = {'class': 'form-control'}
_NUM = {'class': 'form-control'}
_DATE = {'type': 'date', 'class': 'form-control'}


# ---------------------------------------------------------------------------
# FORMULARIOS DE DOCUMENTOS GENERADOS (uno por tipo)
# ---------------------------------------------------------------------------

_CIUDAD_VIII_CHOICES = [
    ('', '--- Seleccionar ciudad ---'),
    ('Concepción', 'Concepción'),
    ('Talcahuano', 'Talcahuano'),
    ('Chiguayante', 'Chiguayante'),
    ('Hualpén', 'Hualpén'),
    ('San Pedro de la Paz', 'San Pedro de la Paz'),
    ('Coronel', 'Coronel'),
    ('Lota', 'Lota'),
    ('Hualqui', 'Hualqui'),
    ('Penco', 'Penco'),
    ('Tomé', 'Tomé'),
    ('Florida', 'Florida'),
    ('Santa Juana', 'Santa Juana'),
    ('Yumbel', 'Yumbel'),
    ('Chillán', 'Chillán'),
    ('Chillán Viejo', 'Chillán Viejo'),
    ('Los Ángeles', 'Los Ángeles'),
    ('Lebu', 'Lebu'),
    ('Cañete', 'Cañete'),
    ('Arauco', 'Arauco'),
    ('Curanilahue', 'Curanilahue'),
    ('Nacimiento', 'Nacimiento'),
    ('Cabrero', 'Cabrero'),
    ('Laja', 'Laja'),
    ('Mulchén', 'Mulchén'),
    ('Otra (VIII Región)', 'Otra (VIII Región)'),
]


_DIAS_CHOICES = [
    ('', '--- Seleccionar ---'),
    ('Lunes a Viernes', 'Lunes a Viernes'),
    ('Lunes a Sábado', 'Lunes a Sábado'),
    ('Lunes a Jueves', 'Lunes a Jueves'),
    ('Lunes a Viernes y sábados alternos', 'Lunes a Viernes y sábados alternos'),
]
_HORAS_CHOICES = [
    ('', '--- Seleccionar ---'),
    ('40 hrs semanales con 1 hr de colación', '40 horas semanales'),
    ('44 hrs semanales con 1 hr de colación', '44 horas semanales'),
    ('45 hrs semanales con 1 hr de colación', '45 horas semanales'),
    ('48 hrs semanales con 1 hr de colación', '48 horas semanales'),
]
_T = [('', '---'),
      ('06:00 HRS', '06:00'), ('06:30 HRS', '06:30'),
      ('07:00 HRS', '07:00'), ('07:30 HRS', '07:30'),
      ('08:00 HRS', '08:00'), ('08:30 HRS', '08:30'), ('09:00 HRS', '09:00'),
      ('12:00 HRS', '12:00'), ('12:30 HRS', '12:30'), ('13:00 HRS', '13:00'), ('13:30 HRS', '13:30'),
      ('14:00 HRS', '14:00'), ('14:30 HRS', '14:30'),
      ('16:00 HRS', '16:00'), ('16:30 HRS', '16:30'),
      ('17:00 HRS', '17:00'), ('17:30 HRS', '17:30'),
      ('18:00 HRS', '18:00'), ('18:30 HRS', '18:30'), ('19:00 HRS', '19:00')]


class ContratoTrabajoForm(forms.Form):
    """Solo pide datos personales variables y horario. Labor, obra, sueldo y
    fechas vienen del Contrato asociado y se muestran como referencia."""
    ciudad_documento  = forms.ChoiceField(label='Ciudad del documento', choices=_CIUDAD_VIII_CHOICES, widget=forms.Select(attrs=_SEL))
    fecha_documento   = forms.DateField(
        label='Fecha del documento',
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={**_INP, 'placeholder': 'dd/mm/aaaa'}),
    )
    estado_civil      = forms.ChoiceField(label='Estado Civil', choices=_ESTADO_CIVIL_CHOICES, widget=forms.Select(attrs=_SEL))
    nacionalidad      = forms.ChoiceField(label='Nacionalidad', choices=_NACIONALIDAD_CHOICES, widget=forms.Select(attrs=_SEL))
    procedencia       = forms.ChoiceField(label='Procedencia / Ciudad de origen', choices=_CIUDAD_CHOICES, widget=forms.Select(attrs=_SEL), required=False)
    ciudad_trabajador = forms.ChoiceField(label='Ciudad de residencia actual', choices=_CIUDAD_CHOICES, widget=forms.Select(attrs=_SEL), required=False)
    domicilio_trabajador = forms.CharField(
        label='Domicilio del trabajador',
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={**_INP, 'placeholder': 'Ej: Av. Los Carrera 1234, Concepción'}),
    )
    prevision         = forms.ChoiceField(label='Previsión (AFP)', choices=_AFP_CHOICES, widget=forms.Select(attrs=_SEL), required=False)
    salud             = forms.ChoiceField(label='Sistema de Salud', choices=_SALUD_CHOICES, widget=forms.Select(attrs=_SEL), required=False)
    # Horario laboral
    dias_laborales    = forms.ChoiceField(label='Días laborales', choices=_DIAS_CHOICES, widget=forms.Select(attrs=_SEL))
    horas_semanales   = forms.ChoiceField(label='Horas semanales', choices=_HORAS_CHOICES, widget=forms.Select(attrs=_SEL))
    inicio_am         = forms.ChoiceField(label='Entrada mañana', choices=_T, initial='08:00 HRS', widget=forms.Select(attrs=_SEL))
    termino_am        = forms.ChoiceField(label='Salida almuerzo', choices=_T, initial='13:00 HRS', widget=forms.Select(attrs=_SEL))
    inicio_pm         = forms.ChoiceField(label='Entrada tarde', choices=_T, initial='14:00 HRS', widget=forms.Select(attrs=_SEL))
    termino_lj        = forms.ChoiceField(label='Salida Lunes–Jueves', choices=_T, initial='18:00 HRS', widget=forms.Select(attrs=_SEL))
    termino_v         = forms.ChoiceField(label='Salida Viernes', choices=_T, initial='17:00 HRS', widget=forms.Select(attrs=_SEL))
    observaciones     = forms.CharField(label='Observaciones / Cláusulas adicionales', required=False, widget=forms.Textarea(attrs={**_INP, 'rows': '2'}))


class AnexoContratoForm(forms.Form):
    ciudad_documento        = forms.ChoiceField(label='Ciudad', choices=_CIUDAD_CHOICES, widget=forms.Select(attrs=_SEL))
    fecha_documento         = forms.DateField(label='Fecha del documento', widget=forms.DateInput(attrs=_DATE))
    fecha_contrato_original = forms.DateField(label='Fecha del contrato original', widget=forms.DateInput(attrs=_DATE))
    monto_colacion          = forms.IntegerField(label='Asignación de Colación ($)', initial=90000, widget=forms.NumberInput(attrs=_NUM))
    monto_movilizacion      = forms.IntegerField(label='Asignación de Movilización ($)', initial=60000, widget=forms.NumberInput(attrs=_NUM))
    monto_herramientas      = forms.IntegerField(label='Desgaste Herramientas ($)', initial=45000, widget=forms.NumberInput(attrs=_NUM))
    observaciones           = forms.CharField(label='Cláusulas adicionales', required=False, widget=forms.Textarea(attrs={**_INP, 'rows': '3'}))


class FiniquitoForm(forms.Form):
    ciudad_documento       = forms.ChoiceField(label='Ciudad', choices=_CIUDAD_CHOICES, widget=forms.Select(attrs=_SEL))
    fecha_documento        = forms.DateField(label='Fecha del documento', widget=forms.DateInput(attrs=_DATE))
    nombre_obra            = forms.CharField(label='Nombre de la obra', max_length=200, widget=forms.TextInput(attrs=_INP))
    especialidad           = forms.CharField(label='Especialidad / Cargo', max_length=150, widget=forms.TextInput(attrs={**_INP, 'placeholder': 'Ej: Maestro Enfierrador'}))
    fecha_inicio_contrato  = forms.DateField(label='Fecha inicio contrato', widget=forms.DateInput(attrs=_DATE))
    fecha_termino_contrato = forms.DateField(label='Fecha término contrato', widget=forms.DateInput(attrs=_DATE))
    causal = forms.ChoiceField(label='Causal de término', choices=[
        ('', '--- Seleccionar causal ---'),
        ('Art. 159 N°5 – Conclusión del trabajo', 'Art. 159 N°5 – Conclusión del trabajo'),
        ('Art. 159 N°1 – Mutuo acuerdo', 'Art. 159 N°1 – Mutuo acuerdo'),
        ('Art. 160 – Sin derecho a indemnización', 'Art. 160 – Sin derecho a indemnización'),
        ('Art. 161 – Necesidades de la empresa', 'Art. 161 – Necesidades de la empresa'),
    ], widget=forms.Select(attrs=_SEL))
    monto_feriado           = forms.DecimalField(label='Feriado proporcional ($)', max_digits=12, decimal_places=0, required=False, initial=0, widget=forms.NumberInput(attrs=_NUM))
    monto_indemnizacion     = forms.DecimalField(label='Indemnización por término ($)', max_digits=12, decimal_places=0, required=False, initial=0, widget=forms.NumberInput(attrs=_NUM))
    otros_montos_descripcion = forms.CharField(label='Otros conceptos', required=False, widget=forms.TextInput(attrs={**_INP, 'placeholder': 'Ej: Horas extras, bonos...'}))
    otros_montos_monto      = forms.DecimalField(label='Monto otros ($)', max_digits=12, decimal_places=0, required=False, initial=0, widget=forms.NumberInput(attrs=_NUM))
    retencion_alimentos     = forms.BooleanField(label='Aplica retención judicial de alimentos (Ley 21.389)', required=False)
    observaciones           = forms.CharField(label='Observaciones', required=False, widget=forms.Textarea(attrs={**_INP, 'rows': '2'}))


class PactoHorasExtrasForm(forms.Form):
    ciudad_documento = forms.ChoiceField(label='Ciudad', choices=_CIUDAD_CHOICES, widget=forms.Select(attrs=_SEL))
    fecha_documento  = forms.DateField(label='Fecha del documento', widget=forms.DateInput(attrs=_DATE))
    horas_diarias    = forms.IntegerField(label='Máximo de horas extra diarias', initial=2, widget=forms.NumberInput(attrs=_NUM))
    duracion_meses   = forms.IntegerField(label='Duración del pacto (meses)', initial=3, widget=forms.NumberInput(attrs=_NUM))
    recargo          = forms.IntegerField(label='Recargo % sobre sueldo ordinario', initial=50, widget=forms.NumberInput(attrs=_NUM))


class ActaEPPForm(forms.Form):
    ciudad_documento = forms.ChoiceField(label='Ciudad', choices=_CIUDAD_CHOICES, widget=forms.Select(attrs=_SEL))
    fecha_documento  = forms.DateField(label='Fecha de entrega', widget=forms.DateInput(attrs=_DATE))
    casco            = forms.BooleanField(label='Casco de Seguridad', required=False, initial=True)
    lentes           = forms.BooleanField(label='Lente de Seguridad', required=False, initial=True)
    chaleco          = forms.BooleanField(label='Chaleco Reflectante', required=False, initial=True)
    zapatos          = forms.BooleanField(label='Zapato de Seguridad', required=False, initial=True)
    guantes          = forms.BooleanField(label='Guante de Seguridad', required=False, initial=True)
    ropa_agua        = forms.BooleanField(label='Ropa de Agua', required=False, initial=False)
    protector_solar  = forms.BooleanField(label='Protector Solar', required=False, initial=True)
    legionario       = forms.BooleanField(label='Legionario', required=False, initial=False)
    bloqueador       = forms.BooleanField(label='Bloqueador Solar', required=False, initial=False)
    fonos            = forms.BooleanField(label='Fonos Auditivos', required=False, initial=False)
    arnes            = forms.BooleanField(label='Arnés de Seguridad', required=False, initial=False)
    cabos            = forms.BooleanField(label='2 Cabos de Vida', required=False, initial=False)
    otros_epp        = forms.CharField(label='Otros elementos (uno por línea)', required=False, widget=forms.Textarea(attrs={**_INP, 'rows': '2', 'placeholder': 'Ej: Careta soldadura\nMáscara respiratoria'}))


class ActaReglamentoForm(forms.Form):
    ciudad_documento = forms.ChoiceField(label='Ciudad', choices=_CIUDAD_CHOICES, widget=forms.Select(attrs=_SEL))
    fecha_documento  = forms.DateField(label='Fecha del acta', widget=forms.DateInput(attrs=_DATE))
    fecha_entrega    = forms.DateField(label='Fecha de entrega del reglamento', widget=forms.DateInput(attrs=_DATE))
