from rest_framework import permissions

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Разрешение: доступ только владельцу объекта или сотруднику (администратор/модератор).
    Сотрудник определяется по флагу is_staff (можно расширить).
    """
    def has_object_permission(self, request, view, obj):
        # Для безопасных методов (GET, HEAD, OPTIONS) доступно владельцу или staff
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or request.user.is_staff
        # Для изменения (PUT, PATCH, DELETE) — только staff
        return request.user.is_staff


class CanChangeApplicationStatus(permissions.BasePermission):
    """
    Разрешение на смену статуса заявки. Только для сотрудников.
    """
    def has_permission(self, request, view):
        # Для действия 'change_status' (кастомный эндпоинт) проверяем is_staff
        if view.action == 'change_status':
            return request.user and request.user.is_staff
        return True

    def has_object_permission(self, request, view, obj):
        # Для объектов — аналогично
        if view.action == 'change_status':
            return request.user.is_staff
        return True


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Только сотрудники могут изменять объекты (POST, PUT, PATCH, DELETE).
    Чтение доступно всем авторизованным (владельцам своих заявок).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff