from django.contrib import admin
from .models import AdoptionApplication, StatusChangeLog

class StatusChangeLogInline(admin.TabularInline):
    model = StatusChangeLog
    extra = 0
    readonly_fields = ('changed_by', 'old_status', 'new_status', 'changed_at', 'note')
    can_delete = False

@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'cat', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'cat__name')
    readonly_fields = ('user', 'cat', 'comment', 'created_at', 'updated_at')
    inlines = [StatusChangeLogInline]
    actions = ['approve_applications', 'reject_applications']

    def approve_applications(self, request, queryset):
        for app in queryset:
            app.status = 'approved'
            app.save()
            StatusChangeLog.objects.create(
                application=app,
                changed_by=request.user,
                old_status='pending',
                new_status='approved',
                note='Одобрено через админ-панель'
            )
        self.message_user(request, f'{queryset.count()} заявок одобрено.')
    approve_applications.short_description = 'Одобрить выбранные заявки'

    def reject_applications(self, request, queryset):
        for app in queryset:
            app.status = 'rejected'
            app.save()
            StatusChangeLog.objects.create(
                application=app,
                changed_by=request.user,
                old_status='pending',
                new_status='rejected',
                note='Отклонено через админ-панель'
            )
        self.message_user(request, f'{queryset.count()} заявок отклонено.')
    reject_applications.short_description = 'Отклонить выбранные заявки'

@admin.register(StatusChangeLog)
class StatusChangeLogAdmin(admin.ModelAdmin):
    list_display = ('application', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('old_status', 'new_status', 'changed_at')
    search_fields = ('application__user__username', 'note')
    readonly_fields = ('application', 'changed_by', 'old_status', 'new_status', 'changed_at', 'note')