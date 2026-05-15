"""
Unit tests for MigrationValidator.
Run with: python -m pytest tests/ -v
"""

import os
import tempfile
import pytest

from src.validator.migration_validator import MigrationValidator


def _create_temp_migrations(files: dict) -> str:
    """Create a temp directory with the given {filename: content} files."""
    tmpdir = tempfile.mkdtemp()
    for filename, content in files.items():
        with open(os.path.join(tmpdir, filename), "w") as fh:
            fh.write(content)
    return tmpdir


class TestNamingConvention:
    def test_valid_names_pass(self):
        tmpdir = _create_temp_migrations({
            "V1__create_users.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);",
            "V2__add_index.sql": "CREATE INDEX idx ON users(id);",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert result.valid

    def test_invalid_name_fails(self):
        tmpdir = _create_temp_migrations({
            "create_users.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert not result.valid
        assert any("Invalid filename format" in e for e in result.errors)

    def test_lowercase_v_fails(self):
        tmpdir = _create_temp_migrations({
            "v1__create_users.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert not result.valid


class TestDuplicateVersions:
    def test_duplicate_version_fails(self):
        tmpdir = _create_temp_migrations({
            "V1__create_users.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);",
            "V1__another_table.sql": "CREATE TABLE another (id SERIAL PRIMARY KEY);",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert not result.valid
        assert any("Duplicate version" in e for e in result.errors)

    def test_unique_versions_pass(self):
        tmpdir = _create_temp_migrations({
            "V1__create_users.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);",
            "V2__create_orders.sql": "CREATE TABLE orders (id SERIAL PRIMARY KEY);",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert result.valid


class TestEmptyFiles:
    def test_empty_file_fails(self):
        tmpdir = _create_temp_migrations({
            "V1__create_users.sql": "",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert not result.valid
        assert any("empty" in e for e in result.errors)

    def test_whitespace_only_fails(self):
        tmpdir = _create_temp_migrations({
            "V1__create_users.sql": "   \n  ",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert not result.valid


class TestDangerousStatements:
    def test_drop_database_warns(self):
        tmpdir = _create_temp_migrations({
            "V1__create_users.sql": "DROP DATABASE mydb;",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert any("DROP DATABASE" in w for w in result.warnings)

    def test_truncate_warns(self):
        tmpdir = _create_temp_migrations({
            "V1__create_users.sql": "TRUNCATE users;",
        })
        result = MigrationValidator(tmpdir).run_all()
        assert any("TRUNCATE" in w for w in result.warnings)


class TestMissingDirectory:
    def test_missing_dir_fails(self):
        result = MigrationValidator("/nonexistent/path").run_all()
        assert not result.valid
        assert any("not found" in e for e in result.errors)


class TestEmptyDirectory:
    def test_empty_dir_warns(self):
        tmpdir = tempfile.mkdtemp()
        result = MigrationValidator(tmpdir).run_all()
        assert result.valid
        assert any("No SQL migration files" in w for w in result.warnings)
