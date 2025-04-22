from typing import Any, TypeAlias

from django.conf import settings
from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.expressions import Col, Expression

if getattr(settings, "DEPRECATED_FIELD_USE_STRUCTLOG", False):
    from structlog import get_logger

    logger = get_logger()
else:
    import logging

    logger = logging.getLogger(__name__)

# Declaring a type alias because model.Fields is defined as a generic type in the stubs
# library, but not in actual implementation. This is a workaround to avoid having to use
# `Any` everywhere, or to have to use some kind of "if TYPE_CHECKING" construct.
FieldType: TypeAlias = "models.Field[Any, Any]"
OptionalFieldType: TypeAlias = "models.Field[Any, Any] | None"


class DeprecatedFieldAccessError(Exception):
    """
    Raised if a deprecated field is accessed in strict mode
    """


def log_or_raise(message_format: str, *args: Any) -> None:
    """
    Either log an error message or if in strict mode raise an exception.
    """

    if getattr(settings, "DEPRECATED_FIELD_STRICT", False):
        message = message_format % args
        raise DeprecatedFieldAccessError(message)

    logger.error(message_format, *args, stack_info=True)


class DeprecatedFieldDescriptor:
    """
    A descriptor for a deprecated field. Logs an error whenever it's accessed
    and always returns None.
    """

    def __init__(self, field: FieldType) -> None:
        self.field = field

    def __get__(
        self, instance: models.Model, owner: type[models.Model] | None = None
    ) -> None:
        if instance:
            log_or_raise(
                'Accessed deprecated field "%s" on instance of "%s.%s"',
                self.field.name,
                instance.__class__.__module__,
                instance.__class__.__qualname__,
            )
        elif owner:
            log_or_raise(
                'Accessed deprecated field "%s" on model class "%s.%s"',
                self.field.name,
                owner.__module__,
                owner.__qualname__,
            )

    def __set__(self, instance: models.Model, value: Any) -> None:
        log_or_raise(
            'Tried to set deprecated field "%s" on instance of "%s.%s"',
            self.field.name,
            instance.__class__.__module__,
            instance.__class__.__qualname__,
        )


class Null(Expression):
    """
    An expression that always returns None.
    """

    def as_sql(self, compiler: Any, connection: Any) -> tuple[str, list[Any]]:
        return "NULL", []


class NullCol(Col, Null):
    """
    A column that always returns None.
    """

    def __init__(
        self, alias: str, target: FieldType, output_field: OptionalFieldType = None
    ):
        super().__init__(alias, target, output_field=output_field)


class DeprecatedField(models.Field):  # type: ignore
    """
    A field that ensures a column can safely be removed from the database in
    a later deploy.

    This ensures that Django does not reference the field in queries by default,
    and if the field is explicitly referenced either an exception is raised or
    an error is raised. The column will still be referenced in the database if
    used in an .update() query, but in all other queries any reference to the
    column is replaced with a NULL literal.
    """

    concrete: bool
    descriptor_class = DeprecatedFieldDescriptor

    def __init__(self, original_field: FieldType) -> None:
        super().__init__()
        self.original_field = original_field

    def contribute_to_class(
        self, cls: type[models.Model], name: str, private_only: bool = False
    ) -> None:
        super().contribute_to_class(cls, name, private_only=private_only)
        self.concrete = False

    def clone(self) -> FieldType:
        """
        This is where the magic happens. Instead of returning a copy of this
        field we return a copy of the underlying field. This method is called
        when the Django migrations system checks for changes, meaning that this
        ensures the deprecation is invisible to the migration system.
        """

        return self.original_field.clone()  # type: ignore

    def get_col(self, alias: str | None, output_field: OptionalFieldType = None) -> Col:
        """
        Hook in to detect when the column is used in a query and replace the
        column reference with null literal in the query.

        Even though the field is marked as concrete=False, Django still allows
        it to be referenced in .values() and .values_list() queries. This will
        catch these cases and either raise an exception or log an error and
        set the selected value to "NULL" in the database query.
        """

        log_or_raise(
            'Deprecated field "%s" on "%s.%s" referenced in query',
            self.name,
            self.model.__module__,
            self.model.__qualname__,
        )
        return NullCol(
            alias="", target=output_field or self, output_field=output_field or self
        )

    def get_db_prep_save(self, value: Any, connection: BaseDatabaseWrapper) -> Any:
        """
        Hook in to detect when the field is used in an update query.

        Even though the field is marked as concrete=False, Django still allows
        it to be referenced in .update(foo=bar) queries. This will catch these
        cases and log or raise an error.
        """

        log_or_raise(
            'Writing to deprecated field "%s" on "%s.%s"',
            self.name,
            self.model.__module__,
            self.model.__qualname__,
        )
        return self.get_db_prep_value(value, connection=connection, prepared=False)

    def value_from_object(self, obj: models.Model) -> None:
        """
        Hook into the logic Django uses to serialize the field in order
        to prevent it from being serialized.

        Django always serializes all fields in the model, so we have to prevent
        it from calling Field.value_from_object(), as this gets the attribute from
        the field, which will raise an error.
        """
        return None

    def get_default(self) -> Any:
        """
        Hook into the logic Django uses to set a value on a model if one wasn't
        provided in __init__, create() or similar. This basically tells Django
        to not set a value, which we don't want for deprecated fields.
        """

        return models.DEFERRED  # type: ignore[attr-defined]


def deprecated(original_field: FieldType) -> DeprecatedField:
    """
    Mark a field as deprecated. This removes the field from queries against the
    database, so we can safely remove it from the database after this change
    has been rolled out.
    """

    # Make sure the original field is nullable
    original_field.null = True

    return DeprecatedField(original_field=original_field)
