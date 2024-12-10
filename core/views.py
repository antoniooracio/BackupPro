from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.core.paginator import Paginator
import os

from .models import equipment, BackupFile, enterprise
from django.conf import settings

from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import Http404, FileResponse
from django.conf import settings

from .models import equipment, BackupFile, enterprise
from .serializers import EquipmentSerializer, EnterpriseSerializer


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    API para listar, criar, atualizar e deletar equipamentos.
    """
    serializer_class = EquipmentSerializer
    queryset = equipment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra os equipamentos para mostrar apenas os da empresa do usuário logado.
        """
        empresa = self.request.user.empresa
        return empresa.get_equipamentos()


class EnterpriseViewSet(viewsets.ModelViewSet):
    """
    API para listar, criar, atualizar e deletar empresas.
    """
    serializer_class = EnterpriseSerializer
    queryset = enterprise.objects.all()
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
def arquivos_backup(request, equipamento_id):
    """
    Lista os arquivos de backup de um equipamento.
    """
    equipamento = get_object_or_404(equipment, id=equipamento_id)
    backup_dir = os.path.join(settings.BASE_DIR, 'backups', equipamento.descricao)

    if not os.path.exists(backup_dir):
        return Response({"detail": "Nenhum backup encontrado."}, status=status.HTTP_404_NOT_FOUND)

    arquivos = sorted(os.listdir(backup_dir))
    query = request.GET.get('q', '').strip().lower()
    if query:
        arquivos = [arquivo for arquivo in arquivos if query in arquivo.lower()]

    return Response({"equipamento": equipamento.descricao, "arquivos": arquivos})


@api_view(['GET'])
def download_backup(request, equipamento_id, arquivo):
    """
    Faz o download de um arquivo de backup.
    """
    equipamento = get_object_or_404(equipment, id=equipamento_id)
    backup_dir = os.path.join(settings.BASE_DIR, 'backups', equipamento.descricao)
    arquivo_path = os.path.join(backup_dir, arquivo)

    if not os.path.exists(arquivo_path):
        raise Http404(f"Arquivo {arquivo} não encontrado.")

    return FileResponse(open(arquivo_path, 'rb'), as_attachment=True, filename=arquivo)








def index(request):
    return render(request, 'index.html')

def contact(request):
    return render(request, 'contact.html')

def enterprise(request):
    return render(request, 'enterprise.html')

def manufacturer(request):
    return render(request, 'manufacturer.html')

def modelEquipment(request):
    return render(request, 'modelEquipment.html')

def Equipment(request):
    # Obtém a empresa do usuário logado
    empresa = request.user.empresa
    # Usa o método get_equipamentos() para buscar os equipamentos
    equipamentos = empresa.get_equipamentos()
    # Renderiza a lista de equipamentos no template
    return render(request, 'equipamentos.html', {'equipamentos': equipamentos})

def error404(request, ex):
    template = loader.get_template('404.html')
    return HttpResponse(content=template.render(), content_type='text/html; charset=utf8', status=404)

def error500(request):
    template = loader.get_template('500.html')
    return HttpResponse(content=template.render(), content_type='text/html; charset=utf8', status=500)



def arquivos_backup(request, equipamento_id):
    """
    Exibe a lista de arquivos de backup para o equipamento selecionado.
    Adiciona funcionalidade de pesquisa e paginação.
    """
    equipamento = get_object_or_404(equipment, id=equipamento_id)
    backup_dir = os.path.join('backups', equipamento.descricao)
    arquivos = []

    if os.path.exists(backup_dir):
        arquivos = sorted(os.listdir(backup_dir))  # Ordena os arquivos por nome

    # Busca
    query = request.GET.get('q', '').strip().lower()
    if query:
        arquivos = [arquivo for arquivo in arquivos if query in arquivo.lower()]

    # Paginação
    paginator = Paginator(arquivos, 10)  # 10 arquivos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/arquivos_backup.html', {
        'equipamento': equipamento,
        'arquivos': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
    })


def download_backup(request, arquivo):
    """
    Permite o download de um arquivo de backup do sistema de arquivos.
    """
    # Extrai o nome do equipamento a partir do nome do arquivo
    nome_equipamento = '_'.join(arquivo.split('_')[:-2])

    # Caminho para a pasta de backups do equipamento
    backup_dir = os.path.join(settings.BASE_DIR, 'backups', nome_equipamento)  # Pasta do equipamento
    arquivo_path = os.path.join(backup_dir, arquivo)

    # Mensagens de depuração
    print(f"Nome do equipamento: {nome_equipamento}")
    print(f"Caminho do diretório de backups: {backup_dir}")
    print(f"Caminho completo do arquivo: {arquivo_path}")

    # Verifica se o arquivo existe no diretório
    if os.path.exists(arquivo_path):
        with open(arquivo_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{arquivo}"'
            return response
    else:
        return HttpResponse(f"Arquivo não encontrado: {arquivo_path}", status=404)