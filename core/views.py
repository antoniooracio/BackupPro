from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.admin.sites import site
import os
from .models import equipment, BackupFile
from django.conf import settings

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
    Restringe o acesso às empresas permitidas para o usuário.
    """
    # Recupera o equipamento
    equipamento = get_object_or_404(equipment, id=equipamento_id)

    # Verifica se o usuário tem permissão para acessar o equipamento
    if not request.user.is_superuser:
        if not hasattr(request.user, 'empresa') or equipamento.enterprise.id != request.user.empresa.id:
            raise Http404("Você não tem permissão para acessar os arquivos deste equipamento.")

    # Caminho para a pasta de backups do equipamento
    backup_dir = os.path.join('backups', equipamento.descricao)  # Pasta específica do equipamento
    arquivos = []

    # Verifica se a pasta existe
    if os.path.exists(backup_dir):
        # Lista todos os arquivos na pasta
        arquivos = os.listdir(backup_dir)

    # Contexto para o template
    context = {
        'equipamento': equipamento,
        'arquivos': arquivos,
        'site_header': site.site_header,
        'site_title': site.site_title,
        'available_apps': site.get_app_list(request),  # Adiciona o contexto necessário
    }

    return render(request, 'core/arquivos_backup.html', context)

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