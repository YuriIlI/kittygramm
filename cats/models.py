from django.contrib.auth import get_user_model
from django.db import models

CHOICES = (
    ('Gray', 'Серый'),
    ('Black', 'Чёрный'),
    ('White', 'Белый'),
    ('Ginger', 'Рыжий'),
    ('Mixed', 'Смешанный'),
)

User = get_user_model()


class Achievement(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Cat(models.Model):
    name = models.CharField(max_length=16)
    color = models.CharField(max_length=16, choices=CHOICES)
    birth_year = models.IntegerField()
    owner = models.ForeignKey(
        User, related_name='cats', on_delete=models.CASCADE)
    achievements = models.ManyToManyField(Achievement, through='AchievementCat')

    def __str__(self):
        return self.name


class AchievementCat(models.Model):
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    cat = models.ForeignKey(Cat, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.achievement} {self.cat}'

# ==================== Новые модели для заявок на усыновление ====================

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class AdoptionApplication(models.Model):
    """
    Модель заявки на усыновление кота.
    """
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('completed', 'Усыновление завершено'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Заявитель'
    )
    cat = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Кот'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус заявки'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий заявителя'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка на усыновление'
        verbose_name_plural = 'Заявки на усыновление'
        # Один пользователь может подать только одну заявку на одного кота
        unique_together = ('user', 'cat')

    def __str__(self):
        return f'Заявка от {self.user.username} на {self.cat.name}'

    def clean(self):
        # Нельзя создать заявку на кота, который уже усыновлён (есть завершённая заявка)
        if self.cat.applications.filter(status='completed').exists():
            raise ValidationError('Этот кот уже усыновлён.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class StatusChangeLog(models.Model):
    """
    Журнал изменений статуса заявки.
    Фиксирует, кто и когда изменил статус, а также старое и новое значение.
    """
    application = models.ForeignKey(
        AdoptionApplication,
        on_delete=models.CASCADE,
        related_name='status_logs',
        verbose_name='Заявка'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='status_changes',
        verbose_name='Кто изменил'
    )
    old_status = models.CharField(
        max_length=20,
        choices=AdoptionApplication.STATUS_CHOICES,
        verbose_name='Старый статус'
    )
    new_status = models.CharField(
        max_length=20,
        choices=AdoptionApplication.STATUS_CHOICES,
        verbose_name='Новый статус'
    )
    changed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата изменения'
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Примечание'
    )

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Запись журнала статусов'
        verbose_name_plural = 'Журнал изменений статусов'

    def __str__(self):
        return f'{self.application} : {self.old_status} -> {self.new_status}'