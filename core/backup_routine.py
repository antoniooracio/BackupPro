import os

import requests
import schedule
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from django.utils import timezone
from core.models import Enterprise
from core.AcessoEquipamentoSSH import acessar_equipamento

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
PASTA_BACKUP = BASE_DIR / "backups"
os.makedirs(PASTA_BACKUP, exist_ok=True)

# Configuração da API
TOKEN = os.getenv("BACKUP_API_TOKEN", "default_token")
SERVER_API_URL = os.getenv("BACKUP_SERVER_API_URL", "http://servidor_principal/api/backups/")


def enviar_arquivo_api(nome_equipamento, arquivo_path, equipamento_id):
    try:
        url = f"{SERVER_API_URL}{equipamento_id}/"
        headers = {"Authorization": f"Token {TOKEN}"}
        files = {"arquivo_backup": open(arquivo_path, "rb")}
        data = {"descricao": nome_equipamento, "data": datetime.now().isoformat()}

        response = requests.post(url, headers=headers, files=files, data=data)
        if response.ok:
            logger.info(f"Backup enviado com sucesso: {arquivo_path}")
        else:
            logger.warning(f"Erro ao enviar arquivo: {response.status_code}. Detalhes: {response.text}")
    except Exception as e:
        logger.error(f"Erro ao enviar arquivo para API: {e}")


def realizar_backup(equipamento):
    logger.info(f"Iniciando backup para {equipamento.descricao} ({equipamento.ip})")
    comando_backup = equipamento.ScriptEquipment.Script
    protocolo = equipamento.access_type.upper()

    try:
        resposta = acessar_equipamento(
            id=equipamento.id,
            ip=equipamento.ip,
            usuario=equipamento.usuarioacesso,
            senha=equipamento.senhaacesso,
            porta=equipamento.portaacesso,
            comando=comando_backup,
            nome_equipamento=equipamento.descricao,
            protocolo=protocolo,
        )
        if resposta:
            caminho_arquivo = salvar_backup(equipamento.descricao, resposta)
            enviar_arquivo_api(equipamento.descricao, caminho_arquivo, equipamento.id)
        else:
            logger.warning(f"Backup não realizado para {equipamento.descricao}. Resposta vazia.")

        equipamento.UltimoBackup = timezone.now()
        equipamento.save()
        logger.info(f"Data do último backup atualizada: {equipamento.descricao}")
    except Exception as e:
        logger.error(f"Erro ao realizar backup para {equipamento.descricao}: {e}")


def salvar_backup(nome_equipamento, conteudo_backup):
    try:
        pasta_equipamento = PASTA_BACKUP / nome_equipamento
        pasta_equipamento.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        arquivo_backup = pasta_equipamento / f"{nome_equipamento}_{timestamp}.txt"
        with arquivo_backup.open("w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo_backup)
        logger.info(f"Backup salvo em {arquivo_backup}")
        return arquivo_backup
    except Exception as e:
        logger.error(f"Erro ao salvar backup: {e}")


def executar_backups():
    from core.models import Equipment
    equipamentos_ativos = Equipment.objects.filter(backup="Sim")
    if not equipamentos_ativos:
        logger.info("Nenhum equipamento ativo para backup.")
        return
    for equipamento in equipamentos_ativos:
        realizar_backup(equipamento)


#def agendar_rotina(horarios=["00:01"]):
#    for horario in horarios:
#        schedule.every().day.at(horario).do(executar_backups)
#        logger.info(f"Rotina de backup agendada para {horario}.")

def agendar_rotina():
    """
    Consulta os horários no banco de dados e agenda a rotina de backups.
    """
    try:
        # Consulta os horários de backup no banco de dados
        horarios = Enterprise.objects.values_list('horario_backup', flat=True).exclude(horario_backup__isnull=True)

        # Limpa agendamentos existentes
        schedule.clear()

        # Configura o agendamento para cada horário encontrado
        for horario in horarios:
            horario_str = horario.strftime("%H:%M")  # Converte TimeField para string no formato HH:MM
            schedule.every().day.at(horario_str).do(executar_backups)
            logger.info(f"Rotina de backup agendada para {horario_str}.")
            print(f"Rotina de backup agendada para {horario_str}.")

        if not horarios:
            logger.warning("Nenhum horário configurado para backup.")
            print("Nenhum horário configurado para backup.")

    except Exception as e:
        logger.error(f"Erro ao agendar a rotina de backups: {e}")
        print(f"Erro ao agendar a rotina de backups: {e}")

def iniciar_thread_agendamento():
    logger.info("Iniciando thread de agendamento.")
    agendamento_thread = threading.Thread(target=agendar_rotina, daemon=True)
    agendamento_thread.start()


if __name__ == "__main__":
    logger.info("Script de rotina de backups iniciado.")
    iniciar_thread_agendamento()
