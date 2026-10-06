from rest_framework import viewsets

from .models import Achievement, Cat, User

from .serializers import AchievementSerializer, CatSerializer, UserSerializer


class CatViewSet(viewsets.ModelViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

# Добавьте недостающие импорты в начало файла
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import AdoptionApplication, StatusChangeLog
from .serializers import (
    AdoptionApplicationSerializer, AdoptionApplicationUpdateSerializer,
    StatusChangeLogSerializer, AdoptionApplicationListSerializer
)
from .permissions import IsOwnerOrStaff, CanChangeApplicationStatus, IsStaffOrReadOnly


class AdoptionApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления заявками на усыновление.
    Доступ:
    - Создание заявки: любой аутентифицированный пользователь.
    - Просмотр списка: пользователь видит только свои заявки, staff — все.
    - Изменение статуса: только staff (через кастомный action change_status).
    - Просмотр истории: владелец заявки или staff.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AdoptionApplication.objects.all()
        return AdoptionApplication.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return AdoptionApplicationListSerializer
        if self.action == 'change_status':
            return AdoptionApplicationUpdateSerializer
        return AdoptionApplicationSerializer

    def get_permissions(self):
        # Для смены статуса используем специальное разрешение
        if self.action == 'change_status':
            permission_classes = [IsAuthenticated, CanChangeApplicationStatus]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['patch'], url_path='change-status')
    def change_status(self, request, pk=None):
        """
        Кастомный эндпоинт для изменения статуса заявки.
        Доступен только сотрудникам (is_staff).
        Тело запроса: {'status': 'approved', 'note': 'Приглашение на встречу'}
        """
        application = self.get_object()
        serializer = self.get_serializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        old_status = application.status
        new_status = serializer.validated_data.get('status')

        if old_status == new_status:
            return Response(
                {'detail': 'Статус не изменён.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем статус
        application.status = new_status
        application.save()

        # Логируем изменение
        StatusChangeLog.objects.create(
            application=application,
            changed_by=request.user,
            old_status=old_status,
            new_status=new_status,
            note=serializer.validated_data.get('note', '')
        )

        return Response(
            {'detail': f'Статус изменён на {application.get_status_display()}.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, url_path='history')
    def history(self, request, pk=None):
        """
        Возвращает историю изменений статуса для конкретной заявки.
        Доступно владельцу заявки или сотруднику.
        """
        application = self.get_object()
        # Проверка прав: владелец или staff
        if not (request.user.is_staff or application.user == request.user):
            return Response(
                {'detail': 'У вас нет прав на просмотр истории этой заявки.'},
                status=status.HTTP_403_FORBIDDEN
            )
        logs = application.status_logs.all()
        serializer = StatusChangeLogSerializer(logs, many=True)
        return Response(serializer.data)