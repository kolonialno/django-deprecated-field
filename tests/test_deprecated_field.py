from unittest import mock

import pytest
from django.test.utils import override_settings

from django_deprecated_field.deprecated_field import DeprecatedFieldAccessError
from tests.app.models import MyModel


@pytest.fixture
def instance() -> MyModel:
    # Mock the logger to prevent it from actually logging errors in the setup stage
    with mock.patch("django_deprecated_field.deprecated_field.logger.error"):
        return MyModel.objects.create(normal_field=1, my_deprecated_field=2)


def test_deprecated_field__clone_nullable() -> None:
    """
    Test that the clone method returns a field that is nullable for deprecated fields.
    """
    # The normal field is untouched
    assert MyModel._meta.get_field("normal_field").clone().null is False  # type: ignore [union-attr]

    # The deprecated field is nullable, although it was originally declared as
    # non-nullable
    assert MyModel._meta.get_field("my_deprecated_field").clone().null is True  # type: ignore [union-attr]


def test_deprecated_field__clone_concrete() -> None:
    """
    Test that the field that is not concrete for deprecated fields.
    """

    assert MyModel._meta.get_field("normal_field").concrete is True
    # Concrete should be set to False for the deprecated field
    assert MyModel._meta.get_field("my_deprecated_field").concrete is False

    sql_query = str(MyModel.objects.all().query)

    # The deprecated field should not be in the query
    assert '"app_mymodel"."my_deprecated_field"' not in sql_query
    # The normal field should be in the query
    assert '"app_mymodel"."normal_field"' in sql_query


@pytest.mark.django_db
def test_deprecated_field__object_access(instance: MyModel) -> None:
    # Normal, simple access should log an error
    with mock.patch(
        "django_deprecated_field.deprecated_field.logger.error"
    ) as mock_logger:
        my_deprecated_field = instance.my_deprecated_field

        # The result is always None, as the field is not accessible
        assert my_deprecated_field is None

        mock_logger.assert_called_once_with(
            'Accessed deprecated field "%s" on instance of "%s.%s"',
            "my_deprecated_field",
            "tests.app.models",
            "MyModel",
            stack_info=True,
        )


@pytest.mark.django_db
@override_settings(DEPRECATED_FIELD_STRICT=True)
def test_deprecated_field__object_access_raises(instance: MyModel) -> None:
    # Normal, simple access should raise an error when strict mode is enabled
    with pytest.raises(DeprecatedFieldAccessError):
        my_deprecated_field = instance.my_deprecated_field

        # The result is always None, as the field is not accessible
        assert my_deprecated_field is None


@pytest.mark.django_db
def test_deprecated_field__query_access() -> None:
    with mock.patch(
        "django_deprecated_field.deprecated_field.logger.error"
    ) as mock_logger:
        MyModel.objects.all().values_list("my_deprecated_field", flat=True)

        mock_logger.assert_called_once_with(
            'Deprecated field "%s" on "%s.%s" referenced in query',
            "my_deprecated_field",
            "tests.app.models",
            "MyModel",
            stack_info=True,
        )


@pytest.mark.django_db
def test_deprecated_field__referenced_write() -> None:
    # Setting a value should log an error
    with mock.patch(
        "django_deprecated_field.deprecated_field.logger.error"
    ) as mock_logger:
        instance = MyModel.objects.create(my_deprecated_field=1, normal_field=2)

        mock_logger.assert_called_once_with(
            'Tried to set deprecated field "%s" on instance of "%s.%s"',
            "my_deprecated_field",
            "tests.app.models",
            "MyModel",
            stack_info=True,
        )
        assert instance.my_deprecated_field is None
