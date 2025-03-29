from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, WalletTransaction,
    BonusTask, BonusCompletion
)


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')


admin.site.register(User, CustomUserAdmin)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'amount', 'description', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('user__username', 'description')


@admin.register(BonusTask)
class BonusTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'reward', 'type', 'code', 'is_active')  # Удалил created_at
    list_filter = ('type', 'is_active')  # Удалил created_at
    search_fields = ('name', 'description', 'code')
    ordering = ['name']  # Убрал created_at


@admin.register(BonusCompletion)
class BonusCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'completed_at')
    list_filter = ('completed_at',)
    search_fields = ('user__username', 'task__name')
    ordering = ['-completed_at']
