import requests
import os
from backup_routine import executar_backups  # Importa sua rotina de backups

# Configurações
API_URL = "http://servidor_principal/api"
TOKEN = "<SEU_TOKEN_DE_AUTENTICACAO>"  # Se necessário

def enviar_arquivo(equipamento_id, caminho_arquivo):
    """
    Envia um arquivo de backup para o sistema principal via API.
    """
    url = f"{API_URL}/backup/{equipamento_id}/"
    headers = {"Authorization": f"Token {TOKEN}"}
    with open(caminho_arquivo, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code == 201:
        print(f"Backup enviado com sucesso: {caminho_arquivo}")
    else:
        print(f"Erro ao enviar backup: {response.status_code} - {response.text}")

def atualizar_ultimo_backup(equipamento_id):
    """
    Atualiza o campo 'ultimo_backup' do equipamento via API.
    """
    url = f"{API_URL}/equipments/{equipamento_id}/update_backup/"
    headers = {"Authorization": f"Token {TOKEN}"}
    response = requests.patch(url, headers=headers)
    if response.status_code == 200:
        print(f"Último backup atualizado para o equipamento {equipamento_id}.")
    else:
        print(f"Erro ao atualizar último backup: {response.status_code} - {response.text}")

def processar_backups():
    """
    Executa os backups e envia os resultados para o sistema principal.
    """
    backups_realizados = executar_backups()  # Lista de dicionários com {'equipamento_id', 'arquivo'}
    for backup in backups_realizados:
        equipamento_id = backup['equipamento_id']
        caminho_arquivo = backup['arquivo']
        enviar_arquivo(equipamento_id, caminho_arquivo)
        atualizar_ultimo_backup(equipamento_id)

if __name__ == "__main__":
    processar_backups()
