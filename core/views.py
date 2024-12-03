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
    Permite pesquisar arquivos pelo nome.
    """
    equipamento = get_object_or_404(equipment, id=equipamento_id)

    # Caminho para a pasta de backups do equipamento
    backup_dir = os.path.join('backups', equipamento.descricao)  # Pasta específica do equipamento
    arquivos = []

    # Verifica se a pasta existe
    if os.path.exists(backup_dir):
        arquivos = os.listdir(backup_dir)

    # Filtra os arquivos pelo termo de pesquisa
    query = request.GET.get('q', '').strip()
    if query:
        arquivos = [arquivo for arquivo in arquivos if query.lower() in arquivo.lower()]

    return render(request, 'core/arquivos_backup.html', {
        'equipamento': equipamento,
        'arquivos': arquivos,
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