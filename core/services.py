from datetime import datetime
from core.models import equipment


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