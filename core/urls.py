from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('', views.dashboard, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Trabajadores
    path('trabajadores/', views.trabajadores_list, name='trabajadores_list'),
    path('trabajadores/check-rut/', views.trabajador_check_rut, name='trabajador_check_rut'),
    path('trabajadores/nuevo/', views.trabajador_create, name='trabajador_create'),
    path('trabajadores/<str:rut>/', views.trabajador_detail, name='trabajador_detail'),
    path('trabajadores/<str:rut>/editar/', views.trabajador_edit, name='trabajador_edit'),
    path('trabajadores/<str:rut>/documentos-masivo/', views.trabajador_upload_doc_masivo, name='trabajador_upload_doc_masivo'),
    path('trabajadores/<str:rut>/strike/', views.trabajador_add_strike, name='trabajador_add_strike'),
    path('trabajadores/<str:rut>/strike/<int:pk>/editar/', views.trabajador_edit_strike, name='trabajador_edit_strike'),
    path('trabajadores/<str:rut>/strike/<int:pk>/toggle/', views.trabajador_toggle_strike, name='trabajador_toggle_strike'),
    path('trabajadores/<str:rut>/lista-negra/ingreso/', views.trabajador_lista_negra_ingreso, name='trabajador_lista_negra_ingreso'),
    path('trabajadores/<str:rut>/lista-negra/salida/', views.trabajador_lista_negra_salida, name='trabajador_lista_negra_salida'),
    path('trabajadores/<str:rut>/descargar-zip/', views.trabajador_download_zip, name='trabajador_download_zip'),
    path('trabajadores/<str:rut>/alertas-cruzadas/', views.trabajador_alertas_cruzadas_ajax, name='trabajador_alertas_cruzadas_ajax'),
    path('trabajadores/<str:rut>/eliminar/', views.trabajador_delete, name='trabajador_delete'),

    # Obras
    path('obras/', views.obras_list, name='obras_list'),
    path('obras/nueva/', views.obra_create, name='obra_create'),
    path('obras/<int:pk>/', views.obra_detail, name='obra_detail'),
    path('obras/<int:pk>/editar/', views.obra_edit, name='obra_edit'),
    path('obras/<int:pk>/cierre-check/', views.obra_cierre_check, name='obra_cierre_check'),
    path('obras/<int:pk>/cerrar/', views.obra_cerrar, name='obra_cerrar'),
    path('obras/<int:pk>/descargar-zip/', views.obra_download_zip, name='obra_download_zip'),
    path('obras/<int:pk>/cierre-mensual/', views.obra_cierre_mensual, name='obra_cierre_mensual'),
    path('obras/<int:pk>/cierre-mensual/<int:cierre_pk>/eliminar/', views.obra_cierre_eliminar, name='obra_cierre_eliminar'),
    path('obras/<int:pk>/planilla-remuneraciones/', views.obra_planilla_remuneraciones, name='obra_planilla_remuneraciones'),
    path('obras/<int:pk>/traslado/', views.obra_traslado_masivo, name='obra_traslado_masivo'),
    path('obras/<int:pk>/traslado/ejecutar/', views.obra_traslado_ejecutar, name='obra_traslado_ejecutar'),
    path('obras/<int:pk>/dotacion-ajax/', views.obra_cierre_dotacion_ajax, name='obra_cierre_dotacion_ajax'),
    path('obras/<int:pk>/nomina-ajax/', views.obra_cierre_nomina_ajax, name='obra_cierre_nomina_ajax'),
    path('obras/<int:pk>/archivar/', views.obra_archivar, name='obra_archivar'),
    path('obras/<int:pk>/check-trabajador/', views.obra_check_trabajador, name='obra_check_trabajador'),
    path('obras/<int:pk>/asignar-trabajador/', views.obra_asignar_trabajador, name='obra_asignar_trabajador'),
    path('obras/<int:pk>/ingreso-rapido/', views.obra_ingreso_rapido, name='obra_ingreso_rapido'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/completar/', views.obra_completar_borrador, name='obra_completar_borrador'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/finalizar/', views.obra_finalizar_contrato, name='obra_finalizar_contrato'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/subir-finiquito/', views.obra_subir_finiquito, name='obra_subir_finiquito'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/resolver-duplicado/', views.obra_resolver_duplicado, name='obra_resolver_duplicado'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/quitar/', views.obra_quitar_trabajador, name='obra_quitar_trabajador'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/licencia/', views.obra_licencia_trabajador, name='obra_licencia_trabajador'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/reactivar/', views.obra_reactivar_trabajador, name='obra_reactivar_trabajador'),
    path('obras/<int:pk>/contrato/<int:contrato_pk>/confirmar-reactivacion/', views.obra_confirmar_reactivacion, name='obra_confirmar_reactivacion'),
    path('obras/<int:pk>/subir-documento/', views.obra_upload_doc, name='obra_upload_doc'),
    path('obras/documento/<int:doc_pk>/eliminar/', views.obra_doc_delete, name='obra_doc_delete'),

    # Contratos
    path('contratos/', views.contratos_list, name='contratos_list'),
    path('contratos/check-duplicado/', views.contrato_check_duplicado, name='contrato_check_duplicado'),
    path('contratos/nuevo/', views.contrato_create, name='contrato_create'),
    path('contratos/<int:pk>/wizard/', views.contrato_wizard, name='contrato_wizard'),
    path('contratos/<int:pk>/editar/', views.contrato_edit, name='contrato_edit'),
    path('contratos/<int:pk>/subir-firmado/', views.contrato_upload_firmado, name='contrato_upload_firmado'),


    # Documentos
    path('documentos/central/', views.documentos_central, name='documentos_central'),
    path('documentos/pendientes/', views.documentos_pendientes, name='documentos_pendientes'),
    path('documentos/batch-download/', views.documentos_batch_download, name='documentos_batch_download'),
    path('documentos/exportar-excel/', views.documentos_exportar_excel, name='documentos_exportar_excel'),
    path('documentos/<int:pk>/descargar/', views.documento_download, name='documento_download'),
    path('documentos/<int:pk>/preview/', views.documento_preview_papelera, name='documento_preview_papelera'),
    path('documentos/<int:pk>/eliminar/', views.documento_delete, name='documento_delete'),
    path('documentos/subir-rapido/', views.documento_upload_rapido, name='documento_upload_rapido'),
    path('documentos/papelera/', views.papelera_documentos, name='papelera_documentos'),
    path('documentos/<int:pk>/restaurar/', views.documento_restore, name='documento_restore'),
    path('documentos/<int:pk>/eliminar-permanente/', views.documento_hard_delete, name='documento_hard_delete'),

    # Bodega
    path('bodega/', views.bodega_index, name='bodega_index'),
    path('bodega/material/guardar/', views.bodega_material_save, name='bodega_material_save'),
    path('bodega/material/<int:pk>/eliminar/', views.bodega_material_delete, name='bodega_material_delete'),
    path('bodega/ingreso-central/', views.bodega_ingreso_central, name='bodega_ingreso_central'),
    path('bodega/asignar-obra/', views.bodega_asignar_obra, name='bodega_asignar_obra'),
    path('bodega/registrar-entrega/', views.bodega_registrar_entrega, name='bodega_registrar_entrega'),
    path('bodega/umbral/<int:bodega_item_id>/', views.bodega_ajuste_umbral, name='bodega_ajuste_umbral'),
    path('bodega/<int:obra_id>/despacho/', views.bodega_despacho, name='bodega_despacho'),
    path('bodega/<int:obra_id>/ingreso/', views.bodega_ingreso_stock, name='bodega_ingreso_stock'),
    path('bodega/<int:obra_id>/capataces/', views.bodega_capataces_ajax, name='bodega_capataces_ajax'),

    # Reportes
    path('reportes/', views.reportes_consolidados, name='reportes_consolidados'),
    path('reportes/exportar-excel/', views.reportes_exportar_excel, name='reportes_exportar_excel'),

    # Empresas (ConfigEmpresa)
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/<int:pk>/editar/', views.empresa_edit, name='empresa_edit'),
    path('empresas/<int:pk>/eliminar/', views.empresa_delete, name='empresa_delete'),

    # Documentos Generados
    path('documentos-empresa/', views.doc_generado_list, name='doc_generado_list'),
    path('documentos-empresa/nuevo/', views.doc_generado_create, name='doc_generado_create'),
    path('documentos-empresa/borradores/', views.doc_generado_borradores, name='doc_generado_borradores'),
    path('documentos-empresa/imprimir-masivo/', views.doc_generado_imprimir_masivo, name='doc_generado_imprimir_masivo'),
    path('documentos-empresa/en-blanco/', views.doc_generado_blank_preview, name='doc_generado_blank_preview'),
    path('documentos-empresa/<int:pk>/editar/', views.doc_generado_edit, name='doc_generado_edit'),
    path('documentos-empresa/<int:pk>/preview/', views.doc_generado_preview, name='doc_generado_preview'),
    path('documentos-empresa/<int:pk>/word/', views.doc_generado_word, name='doc_generado_word'),
    path('documentos-empresa/<int:pk>/pdf/', views.doc_generado_pdf_download, name='doc_generado_pdf_download'),
    path('documentos-empresa/<int:pk>/eliminar/', views.doc_generado_delete, name='doc_generado_delete'),
    path('documentos-empresa/<int:pk>/firmar/', views.doc_generado_firmar, name='doc_generado_firmar'),

    # Licencias Médicas
    path('licencias/', views.licencia_list, name='licencia_list'),
    path('licencias/nueva/', views.licencia_create, name='licencia_create'),
    path('licencias/<int:pk>/', views.licencia_detail, name='licencia_detail'),
    path('licencias/<int:pk>/editar/', views.licencia_edit, name='licencia_edit'),
    path('licencias/<int:pk>/eliminar/', views.licencia_delete, name='licencia_delete'),
    path('licencias/<int:pk>/prorroga/', views.licencia_prorroga, name='licencia_prorroga'),
    path('licencias/trabajador/<str:rut>/ajax/', views.licencias_trabajador_ajax, name='licencias_trabajador_ajax'),

    # Config Remuneraciones
    path('admin-panel/remuneraciones/', views.config_remuneraciones_list, name='config_remuneraciones_list'),
    path('admin-panel/remuneraciones/guardar/', views.config_remuneraciones_save, name='config_remuneraciones_save'),

    # Perfil propio (cualquier usuario autenticado)
    path('perfil/', views.perfil_editar, name='perfil_editar'),

    # Admin Panel
    path('admin-panel/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin-panel/usuarios/nuevo/', views.admin_usuario_create, name='admin_usuario_create'),
    path('admin-panel/usuarios/<int:pk>/editar/', views.admin_usuario_edit, name='admin_usuario_edit'),
    path('admin-panel/usuarios/<int:pk>/toggle/', views.admin_usuario_toggle, name='admin_usuario_toggle'),
    path('admin-panel/catalogos/', views.admin_catalogos, name='admin_catalogos'),
    path('admin-panel/catalogos/tipo-doc/guardar/', views.admin_tipo_documento_save, name='admin_tipo_documento_save'),
    path('admin-panel/catalogos/especialidad/guardar/', views.admin_especialidad_save, name='admin_especialidad_save'),
    path('admin-panel/catalogos/material/guardar/', views.admin_material_save, name='admin_material_save'),
    path('admin-panel/auditoria/', views.admin_auditoria, name='admin_auditoria'),
]
