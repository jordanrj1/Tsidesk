from .dashboard import *
from .trabajadores import *
from .obras import *
from .contratos import *
from .documentos import *
from .bodega import *
from .reportes import *
from .admin_views import *
from .traslados import obra_traslado_masivo, obra_traslado_ejecutar, trabajador_alertas_cruzadas_ajax
from .documentos_generados import (empresa_list, empresa_edit, empresa_delete, doc_generado_list, doc_generado_create, doc_generado_edit, doc_generado_preview, doc_generado_delete, doc_generado_word, doc_generado_pdf_download, doc_generado_firmar, doc_generado_blank_preview, doc_generado_borradores, doc_generado_imprimir_masivo)
from .licencias import (licencia_list, licencia_create, licencia_detail, licencia_edit, licencia_delete, licencia_prorroga, licencias_trabajador_ajax, config_remuneraciones_list, config_remuneraciones_save)
