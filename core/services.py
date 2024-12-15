from datetime import datetime
from core.models import equipment
from .models import Enterprise
from celery import shared_task
from sshtunnel import SSHTunnelForwarder
from celery import current_app
from celery.schedules import crontab
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json
import paramiko


def atualizar_ultimo_backup(equipamento_id):
    """
    Atualiza o campo UltimoBackup do equipamento com a data e hora atuais.
    """
    try:
        equipamento = equipment.objects.get(id=equipamento_id)  # Obtém o equipamento pelo ID
        equipamento.UltimoBackup = datetime.now()  # Atualiza o campo UltimoBackup
        equipamento.save()  # Salva no banco de dados
        print(f"Backup atualizado para o equipamento com ID {equipamento_id}.")
    except equipment.DoesNotExist:
        print(f"Erro: Equipamento com ID {equipamento_id} não encontrado.")



def conectar_com_tunnel(empresa, roteador, comando_backup):
    """
    Estabelece um túnel SSH intermediário (se necessário) e executa o comando no roteador.
    """
    if empresa.usa_tunnel_ssh():
        try:
            # Estabelece um túnel SSH para o servidor intermediário
            with SSHTunnelForwarder(
                (empresa.ssh_intermediario, empresa.porta_ssh),
                ssh_username=empresa.usuario_ssh,
                ssh_password=empresa.senha_ssh,
                remote_bind_address=(roteador.endereco_ip, roteador.porta_ssh)
            ) as tunnel:
                print(f"Túnel SSH estabelecido para {empresa.nome}")
                # Conecta ao roteador através do túnel
                return executar_backup_roteador(
                    '127.0.0.1',  # O túnel redireciona para localhost
                    tunnel.local_bind_port,
                    roteador.usuario_ssh,
                    roteador.senha_ssh,
                    comando_backup
                )
        except Exception as e:
            raise RuntimeError(f"Erro ao estabelecer o túnel SSH para {empresa.nome}: {e}")
    else:
        # Conecta diretamente ao roteador (sem túnel)
        return executar_backup_roteador(
            roteador.endereco_ip,
            roteador.porta_ssh,
            roteador.usuario_ssh,
            roteador.senha_ssh,
            comando_backup
        )


@shared_task
def executar_backups_por_empresa():
    horario_atual = now().time()
    empresas = Enterprise.objects.filter(horario_backup=horario_atual)

    resultados = []

    for empresa in empresas:
        for roteador in empresa.roteadores.all():
            try:
                # Defina o comando de backup
                comando_backup = "comando de backup específico do roteador"

                # Conecte e execute backup
                resultado = conectar_com_tunnel(empresa, roteador, comando_backup)

                # Registre o sucesso
                # BackupTarefa.objects.create(
                #     roteador=roteador,
                #     comando_backup=comando_backup,
                #     status='CONCLUIDO',
                #     ultimo_backup=now()
                # )
                resultados.append(f"Backup concluído para {roteador.nome}: {resultado}")
            except Exception as e:
                # Registre a falha
                # BackupTarefa.objects.create(
                #     roteador=roteador,
                #     comando_backup=comando_backup,
                #     status='FALHOU',
                # )
                resultados.append(f"Erro no backup para {roteador.nome}: {str(e)}")

    return resultados


def agendar_backup(empresa):
    # Apagar qualquer tarefa existente para evitar duplicação
    PeriodicTask.objects.filter(name=f"backup_empresa_{empresa.id}").delete()

    # Criar ou atualizar o agendamento com base no horário do backup
    horario = empresa.horario_backup
    if horario:
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=horario.minute,
            hour=horario.hour,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )

        # Criar a tarefa periódica
        PeriodicTask.objects.create(
            crontab=schedule,
            name=f"backup_empresa_{empresa.id}",
            task="Backup.tasks.realizar_backup",
            args=json.dumps([empresa.id]),  # Passar o ID da empresa como argumento
        )