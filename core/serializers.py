from rest_framework import serializers
from .models import equipment, enterprise

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = equipment
        fields = '__all__'  # Inclui todos os campos do modelo

class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = enterprise
        fields = ['id', 'nome', 'cidade', 'uf', 'ativo']  # Apenas os campos desejados
