import requests

API_URL = "http://127.0.0.1:8000/api/"  # Substitua pelo endereço correto do primeiro sistema
API_TOKEN = "74ed727f0f8104195fb81c47f7cb81ea807d71f7"


def get_equipments():
    """
    Faz uma requisição para listar os equipamentos.
    """
    url = f"{API_URL}equipments/"
    headers = {"Authorization": f"Token {API_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Lista de equipamentos
    else:
        raise Exception(f"Erro ao obter equipamentos: {response.status_code} - {response.text}")


def update_last_backup(equipment_id):
    """
    Atualiza o campo 'UltimoBackup' de um equipamento específico.
    """
    url = f"{API_URL}equipments/{equipment_id}/"
    headers = {"Authorization": f"Token {API_TOKEN}"}
    data = {"UltimoBackup": "2024-12-16T12:00:00Z"}  # Atualize com o timestamp correto

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"Backup atualizado para o equipamento ID {equipment_id}")
    else:
        raise Exception(f"Erro ao atualizar backup: {response.status_code} - {response.text}")


def send_backup_file(equipment_id, file_path):
    """
    Envia um arquivo de backup para o servidor principal.
    """
    url = f"{API_URL}equipments/{equipment_id}/upload/"
    headers = {"Authorization": f"Token {API_TOKEN}"}
    files = {"file": open(file_path, "rb")}  # Certifique-se de que o arquivo existe

    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 201:
        print(f"Arquivo enviado com sucesso para o equipamento ID {equipment_id}")
    else:
        raise Exception(f"Erro ao enviar arquivo: {response.status_code} - {response.text}")
