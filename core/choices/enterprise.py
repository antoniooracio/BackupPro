from django.db import models


class EnterpriseActive(models.TextChoices):
    ATIVO = "Sim"
    DESATIVADO = "Não"
