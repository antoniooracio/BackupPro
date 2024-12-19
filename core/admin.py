from django.contrib import admin, messages
from django.db.models.fields import return_None
from django.urls import reverse
from django.utils.html import format_html
from datetime import datetime, timedelta
from django.contrib.admin import SimpleListFilter
from .models import Enterprise, Manufacturer, ModelEquipment, ScriptEquipment, Equipment, BackupFile


@admin.action(description="Fazer Backup com Script")
def executar_comando_via_ssh(modeladmin, request, queryset):
    """
    Ação personalizada para executar o backup nos equipamentos selecionados.
    """
    for equipamento in queryset:
        if not equipamento.ip or not equipamento.usuarioacesso or not equipamento.senhaacesso:
            messages.warning(request, f"Equipamento {equipamento.descricao} possui dados incompletos de acesso.")
            continue

        try:
            # Executa o comando baseado no script do equipamento e salva a saída em um arquivo
            resultado = equipamento.executar_comando()

            # Mensagem de sucesso
            messages.success(
                request, f"Comando executado com sucesso em {equipamento.descricao}.")

        except Exception as e:
            messages.error(request, f"Erro ao acessar {equipamento.descricao}: {str(e)}")

class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('nome', 'representante', 'cnpj', 'contato', 'email', 'horario_backup', 'ativo')



class EnterpriseListFilter(SimpleListFilter):
    title = 'Proprietário'  # Título exibido no filtro
    parameter_name = 'enterprise'  # Parâmetro na URL

    def lookups(self, request, model_admin):
        """
        Define as opções do filtro.
        Mostra somente as empresas que o usuário pode acessar.
        """
        if request.user.is_superuser:
            # Superusuário vê todas as empresas
            empresas = [(e.id, e.nome) for e in Enterprise.objects.all()]
        elif hasattr(request.user, 'empresa'):
            # Usuário restrito vê apenas sua empresa
            empresas = [(request.user.empresa.id, request.user.empresa.nome)]
        else:
            empresas = []

        # Adiciona separadores se houver mais de uma empresa (apenas para superusuários)
        if len(empresas) > 1 and request.user.is_superuser:
            opcoes = []
            for i, empresa in enumerate(empresas):
                opcoes.append(empresa)
                if i < len(empresas) - 1:
                    opcoes.append(('separator', '------------------'))
            return opcoes

        return empresas

    def queryset(self, request, queryset):
        """
        Filtra os resultados com base na seleção do filtro.
        Ignora o separador.
        """
        if self.value() and self.value() != 'separator':
            return queryset.filter(enterprise__id=self.value())
        return queryset


# Registro no Admin
@admin.register(Equipment)
class equipmentAdmin(admin.ModelAdmin):
    search_fields = ('descricao', 'ip')  # Campo de busca no Admin
    list_display = ('descricao', 'ip_porta', 'usuarioacesso',
                    'enterprise', 'status_backup', 'backup', 'arquivos_link')
    list_filter = (EnterpriseListFilter, )  # Filtro personalizado
    actions = [executar_comando_via_ssh]

    def arquivos_link(self, obj):
        """
        Exibe um botão de link para acessar a página de arquivos de backup do equipamento.
        """
        url = reverse('arquivos_backup', args=[obj.id])
        return format_html('<a class="btn btn-outline-warning btn-sm" href="{}">Arquivos</a>', url)

    arquivos_link.short_description = 'Arquivos'
    arquivos_link.allow_tags = True

    def ip_porta(self, obj):
        """
        Concatena o IP e a Porta de Acesso.
        """
        return f"{obj.ip}:{obj.portaacesso}" if obj.portaacesso else obj.ip
    ip_porta.short_description = "IP:Porta"


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Se o usuário é superusuário ou não tem empresa, mostra todos os equipamentos
        if request.user.is_superuser or not hasattr(request.user, 'empresa'):
            return qs
        # Caso contrário, mostra apenas os equipamentos da empresa do usuário
        return qs.filter(enterprise=request.user.empresa)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Personaliza o campo 'enterprise' para mostrar apenas a empresa do usuário
        if db_field.name == "enterprise":
            if request.user.is_superuser:
                # Se o usuário for superusuário, permite escolher qualquer empresa
                kwargs["queryset"] = Enterprise.objects.all()
            elif hasattr(request.user, 'empresa'):
                # Se o usuário tem uma empresa associada, mostra apenas essa empresa
                kwargs["queryset"] = Enterprise.objects.filter(id=request.user.empresa.id)
            else:
                # Caso o usuário não tenha empresa associada, não exibe nenhuma empresa
                kwargs["queryset"] = Enterprise.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def status_backup(self, obj):
        """
        Exibe um estilo personalizado na linha do Admin com base no campo UltimoBackup.
        Se a data de UltimoBackup anterior a 3 dias atrás, linha vermelha;
        Se a data de UltimoBackup for até 3 dias atrás, linha amarela;
        Se for igual à data de hoje, linha verde.
        """
        if obj.UltimoBackup:
            # Calcula a data de hoje e 2 dias atrás
            hoje = datetime.now().date()  # Utiliza apenas a data, sem a hora
            dois_dias_atras = hoje - timedelta(days=3)

            # Converte o UltimoBackup para apenas a data, sem a hora
            ultimo_backup_data = obj.UltimoBackup.date()

            if ultimo_backup_data == hoje:
                # Data de hoje, linha verde
                return format_html('<span style="color: green;">{}</span>', obj.UltimoBackup.strftime("%d/%m/%Y %H:%M"))
            elif ultimo_backup_data >= dois_dias_atras:
                # Menor que 2 dias, linha amarela
                return format_html('<span style="color: orange;">{}</span>',
                                   obj.UltimoBackup.strftime("%d/%m/%Y %H:%M"))
            else:
                return format_html('<span style="color: red;">{}</span>', obj.UltimoBackup.strftime("%d/%m/%Y %H:%M"))
        return "Nunca"  # Caso não tenha data

        status_backup.short_description = "Último Backup"

    status_backup.short_description = "Último Backup"

    def format_ultimo_backup(self, obj):
        """
        Formata a exibição do campo 'UltimoBackup' no Admin.
        """
        return obj.UltimoBackup.strftime("%d/%m/%Y %H:%M") if obj.UltimoBackup else "Nunca"
    format_ultimo_backup.short_description = "Último Backup"

    def backup_dir(self, obj):
        """
        Exibe o diretório de backup do equipamento no Admin.
        """
        return f"backups/{obj.descricao}/"
    backup_dir.short_description = "Diretório de Backup"


admin.site.register(Enterprise, EnterpriseAdmin)
admin.site.register(Manufacturer)
admin.site.register(ModelEquipment)
admin.site.register(ScriptEquipment)
