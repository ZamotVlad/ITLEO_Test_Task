from rest_framework.permissions import BasePermission


class IsAdminOrOwnTeacher(BasePermission):
    """Admin бачить усе. Teacher — лише обʼєкти своїх груп."""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role.lower() == "admin":
            return True

        if hasattr(obj, "teacher_id"):  # Group
            group = obj
        elif hasattr(obj, "group_id"):  # Student, Schedule
            group = obj.group
        elif hasattr(obj, "student_id"):  # Payment
            group = obj.student.group
        else:
            group = None

        return group is not None and group.teacher_id == request.user.id
