from django.db import models


class EnterpriseActive(models.TextChoices):
    ATIVO = "Sim"
    DESATIVADO = "Não"


class EquipmentBackup(models.TextChoices):
    ACTIVE = "Sim"
    INACTIVE = "Não"
