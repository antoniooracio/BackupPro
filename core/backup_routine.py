import os
from django.core.management.base import BaseCommand
from core.AcessoEquipamentoSSH import acessar_equipamento
import schedule
import time
from datetime import datetime
from django.utils import timezone
import paramiko
import telnetlib
from pathlib import Path
import threading

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
PASTA_BACKUP = BASE_DIR / "backups"
os.makedirs(PASTA_BACKUP, exist_ok=True)  # Garante que a pasta de backups exista

def realizar_backup(equipamento):
    print(f"Iniciando backup para {equipamento.descricao} ({equipamento.ip})")

    comando_backup = equipamento.ScriptEquipment.Script
    protocolo = equipamento.access_type.upper()  # Ex: "SSH" ou "Telnet"

    try:
        # Executa o comando no equipamento
        print(f"Executando comando: {comando_backup}")
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
            print(f"Backup para {equipamento.descricao} realizado com sucesso. Salvando o arquivo...")
            salvar_backup(equipamento.descricao, resposta)
        else:
            print(f"Erro: Resposta vazia para o equipamento {equipamento.descricao}. Backup não realizado.")

        # Atualiza o timestamp do backup
        equipamento.UltimoBackup = timezone.now()
        equipamento.save()
        print(f"Data do último backup atualizada para o equipamento: {equipamento.descricao}")

    except Exception as e:
        print(f"Erro ao realizar backup para {equipamento.descricao}: {str(e)}")


def capturar_resposta(conexao, prompts, tempo_maximo):
    resposta = ""
    inicio = time.time()

    while True:
        if isinstance(conexao, paramiko.Channel) and conexao.recv_ready():
            resposta_parcial = conexao.recv(4096).decode('utf-8')

            # Detecta paginação e envia espaço para continuar
            if "--More--" in resposta_parcial:
                print("Detectado '--More--', enviando espaço via SSH...")
                conexao.send(" ")  # Envia espaço para continuar
                resposta_parcial = resposta_parcial.replace("--More--", "")

            resposta += resposta_parcial
            print(f"Resposta parcial capturada via SSH:\n{resposta_parcial}")

            # Verifica se chegou ao fim do comando
            if any(resposta.strip().endswith(p) for p in prompts):
                print("Comando concluído via SSH.")
                break

        elif isinstance(conexao, telnetlib.Telnet):
            resposta_parcial = conexao.read_very_eager().decode('ascii')

            # Detecta paginação e envia espaço para continuar
            if "--More--" in resposta_parcial:
                print("Detectado '--More--', enviando espaço via Telnet...")
                conexao.write(b" ")  # Envia espaço para continuar
                resposta_parcial = resposta_parcial.replace("--More--", "")

            resposta += resposta_parcial
            print(f"Resposta parcial capturada via Telnet:\n{resposta_parcial}")

            # Verifica se chegou ao fim do comando
            if any(resposta.strip().endswith(p) for p in prompts):
                print("Comando concluído via Telnet.")
                break

        # Verifica tempo limite
        if time.time() - inicio > tempo_maximo:
            raise Exception("Tempo limite excedido ao aguardar resposta do equipamento.")
        time.sleep(0.5)  # Captura mais frequentemente

    return resposta


# Função para salvar o backup em um arquivo dentro da pasta específica do equipamento
def salvar_backup(nome_equipamento, conteudo_backup):
    """
    Salva o conteúdo do backup em um arquivo dentro da pasta do equipamento.
    """
    try:

        # Criação da pasta para o equipamento, se não existir
        pasta_equipamento = PASTA_BACKUP / nome_equipamento
        pasta_equipamento.mkdir(parents=True, exist_ok=True)

        # Gerar o nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        arquivo_backup = pasta_equipamento / f"{nome_equipamento}_{timestamp}.txt"

        # Escrever o conteúdo capturado do equipamento no arquivo
        with arquivo_backup.open("w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo_backup)

        print(f"Backup salvo em {arquivo_backup}")

    except Exception as e:
        print(f"Erro ao salvar o backup: {e}")


# Função para buscar equipamentos ativos e realizar os backups
def executar_backups():
    """
    Busca equipamentos com backup ativo e executa o processo de backup.
    """
    print("Iniciando rotina de backups automáticos...")

    # Importa o modelo 'equipment' dentro da função para evitar erro de apps não carregadas
    from core.models import equipment

    # Consulta os equipamentos ativos no banco de dados
    equipamentos_ativos = equipment.objects.filter(backup="Sim")

    if not equipamentos_ativos:
        print("Nenhum equipamento ativo para backup.")
        return

    # Itera sobre os equipamentos para realizar os backups
    for equipamento in equipamentos_ativos:
        realizar_backup(equipamento)


# Agendar a rotina para rodar diariamente às 00:01
def agendar_rotina():
    """
    Agenda a rotina de backups para rodar todos os dias às 00:01.
    """
    schedule.every().day.at("16:15:00").do(executar_backups)
    print("Rotina de backup agendada para 00:01 diariamente.")

    # Loop infinito para manter o agendamento ativo
    while True:
        schedule.run_pending()
        time.sleep(1)


def iniciar_thread_agendamento():
    """
    Inicia a rotina de agendamento em uma thread separada.
    """
    agendamento_thread = threading.Thread(target=agendar_rotina)
    agendamento_thread.start()

if __name__ == "__main__":
    print("Script de rotina de backups iniciado.")
    iniciar_thread_agendamento()
