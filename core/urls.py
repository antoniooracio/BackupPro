#from html.parser import incomplete
from xml.etree.ElementInclude import include

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls import handler404, handler500
from core import views
from .views import index, contact, modelEquipment, enterprise, manufacturer
from django.conf.urls.static import static
from django.conf import settings
from . import views

from rest_framework.routers import DefaultRouter
from core.views import EquipmentViewSet, EnterpriseViewSet, arquivos_backup, download_backup

router = DefaultRouter()
router.register(r'equipments', EquipmentViewSet)
router.register(r'enterprises', EnterpriseViewSet)




urlpatterns =[
    # Redireciona a raiz para o Django Admin
    #####path('', lambda request: redirect('admin/')),
    # Mantém o restante do seu mapeamento de URLs
    ######path('admin/', admin.site.urls),
    # Outras URLs da sua aplicação, se houver



    path('admin/', admin.site.urls),
    path('', index),
    path('contato', contact),
    path('modelos', modelEquipment),
    path('empresas', enterprise),
    path('fabricantes', manufacturer),
    path('arquivos_backup/<int:equipamento_id>/', views.arquivos_backup, name='arquivos_backup'),
    path('download_backup/<str:arquivo>/', views.download_backup, name='download_backup'),

    path('api/', include(router.urls)),
    path('api/equipments/<uuid:equipamento_id>/backups/', arquivos_backup, name='arquivos-backup'),
    path('api/equipments/<uuid:equipamento_id>/backups/<str:arquivo>/', download_backup, name='download-backup'),

]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'BackPro'
admin.site.site_title = 'Backup Eficiente'
admin.site.index_title = 'Sistema de Backups'