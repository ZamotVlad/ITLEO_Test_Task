class Roles:
    OWNER = "owner"
    MANAGER = "manager"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"

    CHOICES = [
        (OWNER, "Власник"),
        (MANAGER, "Менеджер"),
        (TEACHER, "Викладач"),
        (PARENT, "Батько/мати"),
        (STUDENT, "Студент"),
    ]


OPERATIONAL_ROLES = {Roles.OWNER, Roles.MANAGER}
STAFF_ROLES = {Roles.OWNER, Roles.MANAGER}
