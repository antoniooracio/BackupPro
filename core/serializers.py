from rest_framework import serializers
from .models import Equipment, Enterprise

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'  # Inclui todos os campos do modelo

class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = ['id', 'nome', 'cidade', 'uf', 'ativo']  # Apenas os campos desejados
