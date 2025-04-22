import pytest
from django.db import models

from django_deprecated_field import deprecated

pytestmark = pytest.mark.django_db


class MyModel(models.Model):
    normal_field = models.IntegerField()  # type: ignore [var-annotated]
    my_deprecated_field = deprecated(models.IntegerField(null=False))
