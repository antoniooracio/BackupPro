from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.core.paginator import Paginator
import os
from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework import status
from django.http import Http404, FileResponse
from django.conf import settings
from .models import Equipment, BackupFile, Enterprise
from .serializers import EquipmentSerializer, EnterpriseSerializer
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from pathlib import Path

# View para upload de arquivos
class BackupUploadView(APIView):
    parser_classes = [FileUploadParser]

    def post(self, request, equipamento_id, format=None):
        equipamento = get_object_or_404(Equipment, id=equipamento_id)
        backup_file = request.FILES['file']

        # Salva o arquivo no diretório correspondente
        backup_dir = os.path.join('backups', equipamento.descricao)
        os.makedirs(backup_dir, exist_ok=True)
        with open(os.path.join(backup_dir, backup_file.name), 'wb') as f:
            for chunk in backup_file.chunks():
                f.write(chunk)

        return Response({"message": "Backup recebido com sucesso."}, status=status.HTTP_201_CREATED)


# View para atualizar o último backup
@api_view(['PATCH'])
def update_backup(request, equipamento_id):
    """
    Atualiza o campo 'UltimoBackup' do equipamento com a data/hora fornecida na requisição.
    """
    try:
        equipamento = Equipment.objects.get(id=equipamento_id)  # Busca o equipamento pelo ID
        data_backup = request.data.get("ultimo_backup")  # Obtém o campo 'ultimo_backup' da requisição
        if data_backup:
            # Converte o formato de data/hora e atualiza o campo
            equipamento.UltimoBackup = parse_datetime(data_backup)
            equipamento.save()
            return Response({"mensagem": "Último backup atualizado com sucesso."}, status=200)
        else:
            return Response({"erro": "Campo 'ultimo_backup' não fornecido."}, status=400)
    except Equipment.DoesNotExist:
        return Response({"erro": "Equipamento não encontrado."}, status=404)


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    API para listar, criar, atualizar e deletar equipamentos.
    """
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()
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
    queryset = Enterprise.objects.all()
    serializer_class = EnterpriseSerializer  # Usa o serializer com campos reduzidos
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Permite alternar entre diferentes serializers se necessário.
        """
        # Exemplo: Condicional para usar diferentes serializers (se aplicável)
        return EnterpriseSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def receber_backup(request, equipamento_id):
    arquivo = request.FILES.get('arquivo_backup')
    if not arquivo:
        return Response({"erro": "Nenhum arquivo foi enviado."}, status=400)

    # Salvar o arquivo no servidor principal
    destino = Path(f"backups/{arquivo.name}")
    destino.parent.mkdir(parents=True, exist_ok=True)  # Garante que a pasta exista
    with open(destino, "wb") as f:
        for chunk in arquivo.chunks():
            f.write(chunk)

    # Atualizar o campo "ultimo_backup"
    equipamento = get_object_or_404(Equipment, id=equipamento_id)
    equipamento.ultimo_backup = timezone.now()
    equipamento.save()

    return Response({"mensagem": "Backup recebido com sucesso."}, status=201)


@api_view(['GET'])
def arquivos_backup(request, equipamento_id):
    """
    Lista os arquivos de backup de um equipamento.
    """
    equipamento = get_object_or_404(Equipment, id=equipamento_id)
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
    equipamento = get_object_or_404(Equipment, id=equipamento_id)
    backup_dir = os.path.join(settings.BASE_DIR, 'backups', equipamento.descricao)
    arquivo_path = os.path.join(backup_dir, arquivo)

    if not os.path.exists(arquivo_path):
        raise Http404(f"Arquivo {arquivo} não encontrado.")

    return FileResponse(open(arquivo_path, 'rb'), as_attachment=True, filename=arquivo)


class UpdateUltimoBackupView(APIView):
    def patch(self, request, equipamento_id, format=None):
        equipamento = get_object_or_404(Equipment, id=equipamento_id)
        data_backup = request.data.get("ultimo_backup")
        if data_backup:
            equipamento.UltimoBackup = parse_datetime(data_backup)
            equipamento.save()
            return Response({"mensagem": "Último backup atualizado com sucesso."}, status=HTTP_200_OK)
        return Response({"erro": "Campo 'ultimo_backup' não fornecido."}, status=400)





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

def arquivos_backup(request, equipamento_id):
    """
    Exibe a lista de arquivos de backup para o equipamento selecionado.
    Adiciona funcionalidade de pesquisa e paginação.
    """
    equipamento = get_object_or_404(Equipment, id=equipamento_id)
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

def listar_equipamentos(request):
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