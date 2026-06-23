from rest_framework.permissions import BasePermission

from accounts.roles import Roles


class RoleBasedPermission(BasePermission):
    """
    Замінює IsAdminOrOwnTeacher з Stage 1.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Тільки owner може видаляти
        if request.method == "DELETE" and request.user.role != Roles.OWNER:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == Roles.OWNER:
            return True

        if user.role == Roles.MANAGER:
            return request.method != "DELETE"

        chain = self._resolve(obj)
        if chain is None:
            return False

        if user.role == Roles.TEACHER:
            return chain.get("teacher_id") == user.id

        if user.role == Roles.PARENT:
            return user.id in chain.get("parent_user_ids", [])

        if user.role == Roles.STUDENT:
            return user.id in chain.get("student_user_ids", [])

        return False

    @staticmethod
    def _resolve(obj):
        """
        Повертає словник з ключами для перевірки object-level доступу.
        Використовує list comprehensions та .all() для збереження префетчу з БД.
        """
        from notifications.models import NotificationLog
        from payments.models import Payment
        from schedule.models import Group, Schedule
        from students.models import Parent, Student

        if isinstance(obj, Student):
            return {
                "teacher_id": obj.group.teacher_id if obj.group_id else None,
                "parent_user_ids": [p.user_id for p in obj.parents.all() if p.user_id],
                "student_user_ids": [obj.user_id] if obj.user_id else [],
            }

        if isinstance(obj, Parent):
            return {
                "teacher_id": None,
                "parent_user_ids": [obj.user_id] if obj.user_id else [],
                "student_user_ids": [s.user_id for s in obj.students.all() if s.user_id],
            }

        if isinstance(obj, Group):
            students = obj.students.all()
            return {
                "teacher_id": obj.teacher_id,
                "parent_user_ids": [
                    p.user_id for s in students for p in s.parents.all() if p.user_id
                ],
                "student_user_ids": [s.user_id for s in students if s.user_id],
            }

        if isinstance(obj, Schedule):
            if not obj.group_id:
                return {"teacher_id": None, "parent_user_ids": [], "student_user_ids": []}
            students = obj.group.students.all()
            return {
                "teacher_id": obj.group.teacher_id,
                "parent_user_ids": [
                    p.user_id for s in students for p in s.parents.all() if p.user_id
                ],
                "student_user_ids": [s.user_id for s in students if s.user_id],
            }

        if isinstance(obj, Payment):
            return {
                "teacher_id": None,
                "parent_user_ids": [p.user_id for p in obj.student.parents.all() if p.user_id],
                "student_user_ids": [obj.student.user_id] if obj.student.user_id else [],
            }

        if isinstance(obj, NotificationLog):
            return None  # лише owner/manager

        return None
