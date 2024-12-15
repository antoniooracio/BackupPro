from core.models import Enterprise
from django.dispatch import receiver
from django.db.models.signals import post_save

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Enterprise, EquipmentBackup, EnterpriseActive


@receiver(pre_save, sender=Enterprise)
def status_equipamento_x_status_empresa(instance, **kwargs):
    try:
        # Recupera o registro antigo do banco de dados, caso ele exista
        old_instance = Enterprise.objects.get(pk=instance.pk)
        old_status = old_instance.ativo
        new_status = instance.ativo
        if old_status != new_status:
            # Atualiza os equipamentos com base no novo status da empresa
            novo_status_equipamento = (
                EquipmentBackup.ACTIVE
                if new_status == EnterpriseActive.ATIVO
                else EquipmentBackup.INACTIVE
            )
            instance.equipamento.update(backup=novo_status_equipamento)
            print(f"Equipamentos da empresa '{instance.nome}' atualizados para backup='{novo_status_equipamento}'.")

    except Enterprise.DoesNotExist:
        # Caso seja um novo registro (não existe no banco ainda)
        print("Novo registro sendo criado. Nenhuma ação necessária.")


