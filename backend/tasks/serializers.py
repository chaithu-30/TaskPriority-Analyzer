from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class TaskAnalysisInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    due_date = serializers.DateField()
    estimated_hours = serializers.IntegerField(default=1, min_value=1)
    importance = serializers.IntegerField(default=5, min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        default=list,
        required=False
    )


class TaskAnalysisOutputSerializer(serializers.Serializer):
    title = serializers.CharField()
    due_date = serializers.DateField()
    estimated_hours = serializers.IntegerField()
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.IntegerField())
    priority_score = serializers.FloatField()
    explanation = serializers.CharField()
