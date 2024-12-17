from rest_framework import serializers
from .models import Equipment, Enterprise

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'  # Inclui todos os campos do modelo

class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = ['id', 'nome', 'cidade', 'uf', 'ativo', 'horario_backup']  # Apenas os campos desejados
