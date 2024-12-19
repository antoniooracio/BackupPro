from rest_framework import serializers
from .models import Equipment, Enterprise, ScriptEquipment

class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = ['id', 'nome', 'cidade', 'uf', 'ativo', 'horario_backup']  # Apenas os campos desejados

class ScriptEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScriptEquipment
        fields = ['Script',]


class EquipmentSerializer(serializers.ModelSerializer):
    ScriptEquipment = ScriptEquipmentSerializer()

    class Meta:
        model = Equipment
        fields = '__all__'  # Inclui todos os campos do modelo
