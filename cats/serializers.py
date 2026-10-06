from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

import datetime as dt

from .models import CHOICES, Achievement, AchievementCat, Cat, User


class UserSerializer(serializers.ModelSerializer):
    cats = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'cats')
        ref_name = 'ReadOnlyUsers'


class AchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class CatSerializer(serializers.ModelSerializer):
    achievements = AchievementSerializer(many=True, required=False)
    color = serializers.ChoiceField(choices=CHOICES)
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year', 'achievements', 'owner',
                  'age')

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    def create(self, validated_data):
        if 'achievements' not in self.initial_data:
            cat = Cat.objects.create(**validated_data)
            return cat
        else:
            achievements = validated_data.pop('achievements')
            cat = Cat.objects.create(**validated_data)
            for achievement in achievements:
                current_achievement, status = Achievement.objects.get_or_create(
                    **achievement)
                AchievementCat.objects.create(
                    achievement=current_achievement, cat=cat)
            return cat

# ==================== Сериализаторы для заявок ====================

from .models import AdoptionApplication, StatusChangeLog
from rest_framework import serializers

class StatusChangeLogSerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = StatusChangeLog
        fields = ['id', 'old_status', 'new_status', 'changed_by', 'changed_at', 'note']
        read_only_fields = ['id', 'changed_at']


class AdoptionApplicationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    cat_name = serializers.ReadOnlyField(source='cat.name')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_logs = StatusChangeLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = AdoptionApplication
        fields = [
            'id', 'user', 'cat', 'cat_name', 'status', 'status_display',
            'comment', 'created_at', 'updated_at', 'status_logs'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'status']

    def validate_cat(self, value):
        """Проверка: нельзя подать заявку на уже усыновлённого кота."""
        if value.applications.filter(status='completed').exists():
            raise serializers.ValidationError('Этот кот уже усыновлён.')
        return value

    def validate(self, data):
        # Дополнительная проверка уникальности пары (user, cat) на уровне сериализатора
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            cat = data.get('cat')
            if AdoptionApplication.objects.filter(user=request.user, cat=cat).exists():
                raise serializers.ValidationError(
                    {'cat': 'Вы уже подавали заявку на этого кота.'}
                )
        return data

    def create(self, validated_data):
        # Автоматически подставляем текущего пользователя
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class AdoptionApplicationUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор только для смены статуса (используется администратором)."""
    class Meta:
        model = AdoptionApplication
        fields = ['status', 'comment']


class AdoptionApplicationListSerializer(AdoptionApplicationSerializer):
    """Списочный вариант – без подробной истории статусов (оптимизация)."""
    class Meta(AdoptionApplicationSerializer.Meta):
        fields = [
            'id', 'user', 'cat', 'cat_name', 'status', 'status_display',
            'comment', 'created_at', 'updated_at'
        ]