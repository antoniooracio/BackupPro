import uuid
from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE
from .AcessoEquipamentoSSH import acessar_equipamento
from django.utils import timezone

import os
from datetime import datetime

class manufacturer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField('Nome do Fabricante', max_length=100)

    def __str__(self):
        return self.nome
    class Meta:
        verbose_name = "Fabricánte"
        verbose_name_plural = "Fabricántes"

class modelEquipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modelo = models.CharField('Modelo', max_length=100)
    manufacturer = models.ForeignKey(manufacturer, on_delete=models.CASCADE)

    def __str__(self):
        return self.modelo
    class Meta:
        verbose_name = "Modelo de Equipamento"
        verbose_name_plural = "Modelo de Equipamentos"

class ScriptEquipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Script = models.TextField('Script do Backup', blank=True, null=True)
    modelEquipment = models.ForeignKey(modelEquipment, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.modelEquipment)
    class Meta:
        verbose_name = "Script"
        verbose_name_plural = "Scripts"

class EnterpriseActive(models.TextChoices):
        ATIVO = "Sim"
        DESATIVADO = "Não"

class enterprise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField('Nome da empresa', max_length=100)
    uf = models.CharField('Estado', max_length=2)
    cidade = models.CharField('Cidade', max_length=100)
    endereco = models.CharField('Endereço', max_length=400)
    cnpj = models.CharField('CNPJ', max_length=18)
    representante = models.CharField('Nome do representante', max_length=50)
    contato = models.CharField('Telefone', max_length=12)
    email = models.CharField('E-mail',max_length=60,  blank=True, null=True)
    ativo = models.CharField('Status', max_length=20,
                              choices=EnterpriseActive.choices,
                              default=EnterpriseActive.ATIVO)
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuário responsável",
        related_name="empresa"
    )


    def get_equipamentos(self):
        # Retorna todos os equipamentos relacionados a essa empresa
        return self.equipamento.all()
    def __str__(self):
        return f'{self.nome} {self.representante}'
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

class EquipmentBackup(models.TextChoices):
    ACTIVE = "Sim"
    INACTIVE = "Não"


class equipment(models.Model):
    descricao = models.CharField('Nome do equipamento', max_length=30)
    ip = models.CharField('IP de acesso', max_length=30,  blank=True, null=True)
    portaacesso = models.CharField('Porta SSH', max_length=6,  blank=True, null=True)

    ACCESS_TYPE_CHOICES = [
        ('Telnet', 'Telnet'),
        ('SSH', 'SSH'),
    ]
    access_type = models.CharField(
        max_length=10,
        choices=ACCESS_TYPE_CHOICES,
        default='SSH',
        verbose_name='Tipo de Acesso'
    )

    usuarioacesso = models.CharField('Usuário de acesso', max_length=20,  blank=True, null=True)
    senhaacesso = models.CharField('Senha de acesso', max_length=30,  blank=True, null=True)
    backup = models.CharField(max_length=20,
                              choices=EquipmentBackup.choices,
                              default=EquipmentBackup.ACTIVE)
    UltimoBackup = models.DateTimeField('Data Último Backup')

    enterprise = models.ForeignKey(enterprise, on_delete=CASCADE, related_name="equipamento", verbose_name='Proprietário')
    modelEquipment = models.ForeignKey(modelEquipment, on_delete=CASCADE, verbose_name='Modelo')
    ScriptEquipment = models.ForeignKey(ScriptEquipment, on_delete=CASCADE, verbose_name='Script', default='1db5796166b34da1a3f7828c7469c506')

    def __str__(self):
        return f'{self.descricao} {self.ip} (ID: {self.id})'

    class Meta:
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"

    def executar_comando(self):
        """
        Executa o comando associado ao equipamento usando o protocolo definido.
        Atualiza o campo UltimoBackup após a execução bem-sucedida.
        """
        if not self.ip or not self.usuarioacesso or not self.senhaacesso:
            return "Dados de acesso incompletos para o equipamento."

        if not self.ScriptEquipment or not self.ScriptEquipment.Script:
            return "Nenhum script de comando definido para o equipamento."

        comando = self.ScriptEquipment.Script  # Recupera o script do campo ScriptEquipment
        porta = int(self.portaacesso) if self.portaacesso else (23 if self.access_type == "Telnet" else 22)

        try:
            if self.access_type == "SSH":
                print(f"Capturando mensagem inicial via SSH...")
                resultado = acessar_equipamento(
                    id=self.id,
                    ip=self.ip,
                    usuario=self.usuarioacesso,
                    senha=self.senhaacesso,
                    porta=porta,
                    comando=comando,
                    nome_equipamento=self.descricao,
                    protocolo="SSH"
                )
            elif self.access_type == "Telnet":
                print(f"Capturando mensagem inicial via Telnet...")
                resultado = acessar_equipamento(
                    id=self.id,
                    ip=self.ip,
                    usuario=self.usuarioacesso,
                    senha=self.senhaacesso,
                    porta=porta,
                    comando=comando,
                    nome_equipamento=self.descricao,
                    protocolo="Telnet"
                )
            else:
                raise ValueError(f"Tipo de acesso inválido: {self.access_type}")

            # Salva o backup em arquivo
            base_dir = "backups/"
            equipamento_dir = os.path.join(base_dir, self.descricao)
            os.makedirs(equipamento_dir, exist_ok=True)
            arquivo_saida = os.path.join(
                equipamento_dir, f"{self.descricao}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            with open(arquivo_saida, "w", encoding="utf-8") as arquivo:
                arquivo.write(resultado)

            # Atualiza o campo UltimoBackup diretamente no modelo
            self.UltimoBackup = timezone.now()  # Use timezone.now() para evitar problemas de fuso horário
            self.save()  # Salva o objeto atualizado no banco de dados

            return resultado
        except Exception as e:
            raise RuntimeError(f"Erro ao acessar o equipamento: {str(e)}")


class BackupFile(models.Model):
    equipamento = models.ForeignKey('equipment', on_delete=models.CASCADE, related_name="backup_files")
    file = models.FileField(upload_to='backups/', max_length=500)  # Salva os arquivos na pasta 'backups/'
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Backup de {self.equipamento.descricao} - {self.uploaded_at.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Arquivo de Backup"
        verbose_name_plural = "Arquivos de Backup"