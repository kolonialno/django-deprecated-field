# Django Deprecated Field

A Django field util that allows you to mark model fields as deprecated. This will enable you to have migration consistency when using rolling deploy.

## Motivation

When you have multiple instances of Django running, for redundancy, you typically deploy new versions in a rolling manner. One instance will be updated to the new versions before the other, and for a period, you will be running both the new and the old version in parallel. Normally, the database migrations will be run before any of the Django instances are updated. This poses a problem for certain types of database migrations, since your database schema needs to support both versions at all times.

One of these problematic migrations is deleting a column from a table. You can quickly end up in a situation where the row has been deleted from the table with the migration, and you have one Django instance to expects it to still exist. Since Django enumerates all known fields in database queries (`SELECT field1, field2 FROM ...` not `SELECT * FROM ...`), the instance with the old version will generate queries that aren't consistent with the database schema, and will fail.

One approach to this can be to first deploy a version that has the field removed from the Django model class, but doesn't include the accompanying database migration file. That will remove the Django instances' dependency on the field. Then, in a second deploy that contains the migration file, the column is actually deleted from the database table.

However, this means that you have to allow builds/deploys that have inconsistencies between the Django models in the code, and the migrations. That can lead to a lot of other, unwanted inconsistencies.

`django-deprecated-field` solves this problem, by introducing the notion of a field being "deprecated, marked for deletion". 

## Features

When a field is deprecated, we:
- Ensure that is is nullable, which is necessary for cross-version compatibility for `INSERT`s
- Omit the field from `SELECT`s and other queries, ensuring cross-version compatibility for `SELECT`s, etc
- Log a warning, or raise an exception, if the deprecated field is accessed in any code

## Usage

### Mark a field as deprecated:

```python
from django.db import models
from django_deprecated_field import deprecated

class MyClass(models.Model):

    my_field = deprecated(
        models.CharField(...)
    )
```

The `deprecated()` field will return a new version of the `CharField` that ensures that it will be compatible with both new and old versions. If the field wasn't nullable before, it will become so now, so you may have to generate a new migration `python manage.py makemigrations`.

After deploying this version to production, you are free to delete the field definition, make a new migrations, and deploy the version that deletes the field.

### Configuration

#### `DEPRECATED_FIELD_STRICT`
Boolean. Default: `False`. 

Set to `True` to raise an exception whenever the field is accessed in the code. Setting it to `False` will trigger a `ERROR` log. It's recommended to set this to `True` in development, CI and staging, and to `False` in production.

#### `DEPRECATED_FIELD_USE_STRUCTLOG`
Boolean. Default: `False`. 

Set to `True` to use `structlog` instead of the standard `logging` module for logging.

## Installation

### Using pip
```bash
pip install django-deprecated-field
```

### Using uv (recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the package
uv pip install django-deprecated-field
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/kolonialno/django-deprecated-field.git
cd django-deprecated-field
```

2. Install and setup asdf (if not already installed):
```bash
# Install asdf
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.13.1
echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc  # or ~/.zshrc for Zsh
echo '. "$HOME/.asdf/completions/asdf.bash"' >> ~/.bashrc  # or ~/.zshrc for Zsh

# Install plugins
asdf plugin add python
asdf plugin add uv https://github.com/looztra/asdf-uv.git
asdf plugin add direnv

# Install Python and uv versions specified in .tool-versions
asdf install
```

3. Allow direnv
```bash
direnv allow
```

4. Install development dependencies using uv:
```bash
# Install the packagse with development dependencies
uv sync --dev
```


## Development

The project uses several tools to maintain code quality:

- `ruff` for linting and code formatting (replaces black and isort)
- `mypy` for type checking
- `pytest` for testing

All tools are configured in `pyproject.toml`.

### Code Quality

To check and fix code quality issues:
```bash
# Check for issues
ruff check .

# Fix issues automatically
ruff check --fix .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Pull Request Title Requirement

We require the Pull Request titles to follow the [Conventional Commit specification](https://www.conventionalcommits.org/en/v1.0.0/), and there's a CI check that enforces this.

The very short version of that is that your PR title must be prefixed with `fix:`, `feat:` or `BREAKING CHANGE:`, depending on what you're doing. This will be the basis for the release (semantic) version, and the automatic changelog. Please see the specification for more details.

## Releasing

When changes are committed to main, a release PR for the package is automatically created, using [Release Please](https://github.com/googleapis/release-please). The [changelog](CHANGELOG.md) is also automatically updated. When we're ready to package your changes into a release and distribute it to users, that PR will be merged.

A new distributable package will be built, and and published to PyPi.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details. 