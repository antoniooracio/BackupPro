import time
from datetime import datetime
import requests
from backup_routine import executar_backups  # Rotina específica dos backups


# Configurações
API_URL = "http://177.52.216.4/api"
TOKEN = "98c9cdee71132b4fbaa2b1a98577c786425a76fb"  # Substitua pelo token correspondente


headers = {"Authorization": f"Token {TOKEN}"}


def obter_horario_backup():
    """
    Consulta o horário de backup da empresa associada ao token.
    """
    url = f"{API_URL}/enterprises/horario_backup/"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("horario")
    else:
        print(f"Erro ao obter horário de backup: {response.status_code} - {response.text}")
        return None


def obter_equipamentos_ativos():
    """
    Consulta os equipamentos ativos da empresa associada ao token.
    """
    url = f"{API_URL}/equipments/ativos/"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Espera uma lista de dicionários com os dados dos equipamentos
    else:
        print(f"Erro ao obter equipamentos: {response.status_code} - {response.text}")
        return []


def enviar_arquivo(equipamento_id, caminho_arquivo):
    """
    Envia o arquivo de backup para o servidor principal.
    """
    url = f"{API_URL}/backup/{equipamento_id}/"
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
    response = requests.patch(url, headers=headers)
    if response.status_code == 200:
        print(f"Último backup atualizado para o equipamento {equipamento_id}.")
    else:
        print(f"Erro ao atualizar último backup: {response.status_code} - {response.text}")


def processar_backups():
    """
    Executa os backups com base nos dados obtidos da API.
    """
    horario_backup = obter_horario_backup()
    if not horario_backup:
        print("Não foi possível obter o horário de backup.")
        return

    while True:
        now = datetime.now().strftime("%H:%M")
        if now == horario_backup:
            equipamentos = obter_equipamentos_ativos()
            for equipamento in equipamentos:
                equipamento_id = equipamento['id']
                nome = equipamento['nome']
                ip = equipamento['ip']
                print(f"Executando backup para o equipamento: {nome} ({ip})")

                backups_realizados = executar_backups(equipamento)  # Chama sua rotina de backups
                for backup in backups_realizados:
                    caminho_arquivo = backup['arquivo']
                    enviar_arquivo(equipamento_id, caminho_arquivo)
                    atualizar_ultimo_backup(equipamento_id)

            print(f"Backups concluídos às {horario_backup}.")
            time.sleep(60)  # Evita rodar várias vezes no mesmo minuto
        else:
            time.sleep(30)  # Checa novamente em 30 segundos


if __name__ == "__main__":
    processar_backups()