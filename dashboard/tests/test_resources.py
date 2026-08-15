import pytest

from dashboard.resources import VerboseNameResource
from students.models import Student


class StudentTestResource(VerboseNameResource):
    class Meta:
        model = Student


@pytest.mark.django_db
def test_column_names_use_verbose_name():
    resource = StudentTestResource()

    field = resource.fields["full_name"]

    assert field.column_name == "Повне ім'я"
