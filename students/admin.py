import secrets
import string

from django.contrib import admin, messages
from django.core.mail import send_mail
from django.db import transaction
from import_export.admin import ExportMixin
from unfold.admin import ModelAdmin

from accounts.models import User
from accounts.roles import OPERATIONAL_ROLES, Roles
from dashboard.resources import VerboseNameResource
from students.models import Course, Parent, Student
from students.services import scope_students


class StudentResource(VerboseNameResource):
    class Meta:
        model = Student


class ParentResource(VerboseNameResource):
    class Meta:
        model = Parent


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@admin.action(description="Створити логін і надіслати запрошення на email")
def create_login_action(modeladmin, request, queryset):
    created = 0
    skipped = 0

    for obj in queryset.filter(user__isnull=True):
        email = getattr(obj, "email", "")
        if not email:
            skipped += 1
            continue
        if User.objects.filter(email=email).exists():
            skipped += 1
            continue

        role = Roles.PARENT if isinstance(obj, Parent) else Roles.STUDENT
        password = _generate_password()

        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                role=role,
            )
            obj.user = user
            obj.save(update_fields=["user"])

        send_mail(
            subject="Запрошення до Academy",
            message=(
                f"Вітаємо!\n\n"
                f"Ваш акаунт створено.\n"
                f"Логін: {email}\n"
                f"Пароль: {password}\n\n"
                f"Будь ласка, змініть пароль після першого входу."
            ),
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )
        created += 1

    modeladmin.message_user(
        request,
        f"Створено: {created}, пропущено: {skipped}",
        messages.SUCCESS,
    )


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    def has_view_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_add_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def has_change_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER

    def delete_model(self, request, obj):
        obj.soft_delete(user=request.user)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.soft_delete(user=request.user)


@admin.register(Student)
class StudentAdmin(ExportMixin, ModelAdmin):
    resource_class = StudentResource
    list_display = ("full_name", "course", "group", "status", "email", "user")
    list_filter = ("status", "course", "group")
    search_fields = ("full_name", "phone", "telegram_username", "email")
    actions = [create_login_action]

    def has_view_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_add_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def has_change_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER

    def has_export_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def get_queryset(self, request):
        return scope_students(request.user)

    def delete_model(self, request, obj):
        obj.soft_delete(user=request.user)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.soft_delete(user=request.user)


@admin.register(Parent)
class ParentAdmin(ExportMixin, ModelAdmin):
    resource_class = ParentResource
    list_display = ("full_name", "phone", "email", "user")
    search_fields = ("full_name", "phone", "email")
    actions = [create_login_action]

    def has_view_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_add_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def has_change_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER

    def has_export_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def delete_model(self, request, obj):
        obj.soft_delete(user=request.user)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.soft_delete(user=request.user)
