"""
Accounts App Admin - Teacher Profile Administration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Teacher


class TeacherInline(admin.StackedInline):
    """Inline admin for Teacher profile"""
    model = Teacher
    can_delete = False
    verbose_name_plural = 'Teacher Profile'
    fields = ('full_name', 'department', 'phone', 'profile_picture', 'is_super_admin')


class UserAdmin(BaseUserAdmin):
    """Custom User admin with Teacher inline"""
    inlines = (TeacherInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'teacher__is_super_admin')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'teacher__full_name')
    ordering = ('-date_joined',)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Standalone Teacher admin"""
    list_display = ('full_name', 'email', 'department', 'phone', 'is_super_admin', 'created_at')
    list_filter = ('is_super_admin', 'department', 'created_at')
    search_fields = ('full_name', 'user__email', 'department')
    readonly_fields = ('created_at', 'updated_at', 'user')
    
    def email(self, obj):
        return obj.user.email
    
    email.admin_order_field = 'user__email'
    email.short_description = 'Email'
