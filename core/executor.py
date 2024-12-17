import time
from datetime import datetime
import requests
from backup_routine import executar_backups  # Rotina específica dos backups
import os
import django
import sys


# Adiciona o caminho do seu projeto no sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Backup')))
# Definir o DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Backup.settings")
# Configurar o Django
django.setup()


# Configurações
API_URL = "http://177.52.216.4/api"
TOKEN = "98c9cdee71132b4fbaa2b1a98577c786425a76fb"  # Substitua pelo token correspondente


headers = {"Authorization": f"Token {TOKEN}"}


# Função para verificar se o backup já foi feito hoje
def backup_hoje_realizado():
    """Verifica se o backup já foi feito hoje, armazenando a data do último backup em um arquivo"""
    data_hoje = datetime.now().date()
    arquivo_backup = "ultimo_backup.txt"

    # Verifica se o arquivo existe e lê a data do último backup
    if os.path.exists(arquivo_backup):
        with open(arquivo_backup, 'r') as f:
            data_ultimo_backup = f.read().strip()
            # Se o último backup foi realizado hoje, retorna True
            if data_ultimo_backup == str(data_hoje):
                return True
    return False


# Função para atualizar a data do último backup
def atualizar_data_ultimo_backup():
    """Atualiza a data do último backup realizado no arquivo"""
    data_hoje = datetime.now().date()
    with open("ultimo_backup.txt", 'w') as f:
        f.write(str(data_hoje))


def obter_horario_backup():
    """
    Consulta o horário de backup da empresa associada ao token e retorna apenas o campo desejado.
    """
    url = f"{API_URL}/enterprises/"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        empresas = response.json()  # Converte a resposta em JSON
        if empresas and isinstance(empresas, list):
            horario_backup = empresas[0].get("horario_backup")  # Pega o primeiro horário de backup
            print(f"Rotina agendada para : {horario_backup}")
            return horario_backup
        else:
            print("Nenhuma empresa encontrada ou dados mal formatados.")
            return None
    else:
        print(f"Erro ao obter empresas: {response.status_code} - {response.text}")
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
    Verifica o horário agendado e executa os backups, mas apenas uma vez por dia.
    """
    horario_agendado = obter_horario_backup()
    if not horario_agendado:
        print("Não foi possível obter o horário de backup.")
        return

    print(f"Rotina agendada para: {horario_agendado}")

    while True:
        # Verifica se o backup já foi realizado hoje
        if backup_hoje_realizado():
            print("Backup já realizado hoje. Aguardando amanhã...")
            time.sleep(86400)  # Aguardar 24 horas (86400 segundos) para o próximo dia
            continue  # Reinicia o loop para verificar o horário do novo dia

        agora = datetime.now().strftime("%H:%M:%S")
        print(f"Horário atual: {agora}")

        # Verifica se o horário atual é o mesmo que o agendado, com uma pequena margem de erro
        if agora == horario_agendado:
            print("Horário alcançado! Executando backups...")
            backups_realizados = executar_backups()
            print(f"Backups realizados: {backups_realizados}")
            atualizar_data_ultimo_backup()  # Atualiza a data do último backup
            time.sleep(60)  # Evita execução duplicada no mesmo minuto
        elif agora > horario_agendado:
            print("O horário agendado passou. Executando os backups!")
            backups_realizados = executar_backups()
            print(f"Backups realizados: {backups_realizados}")
            atualizar_data_ultimo_backup()  # Atualiza a data do último backup
            time.sleep(60)  # Evita execução duplicada
        else:
            print("Ainda não é o horário agendado. Aguardando...")
            time.sleep(30)  # Checa novamente em 30 segundos


if __name__ == "__main__":
    processar_backups()