from core.models import Enterprise
from django.dispatch import receiver
from django.db.models.signals import post_save



@receiver(post_save, sender=Enterprise)
def status_equipamento_x_status_empresa(instance, **kwargs):
    if not kwargs['created']:  # Garante que estamos lidando com um registro existente
        old_status = Enterprise.objects.get(pk=instance.pk).ativo
        if old_status != instance.ativo:
            # Se o status mudou, sincroniza os equipamentos
            novo_status_equipamento = EquipmentBackup.ACTIVE if instance.ativo == EnterpriseActive.ATIVO else EquipmentBackup.INACTIVE
            instance.equipamento.update(backup=novo_status_equipamento)
            print(f"Equipamentos da empresa '{instance.nome}' atualizados para backup='{novo_status_equipamento}'.")
        instance.save()
    
