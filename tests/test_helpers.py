"""Unit tests for helper utilities."""

import os
import tempfile
import pytest

from src.utils.helpers import (
    compute_checksum,
    format_duration,
    get_sorted_migration_files,
    mask_password,
    split_sql_statements,
)


class TestComputeChecksum:
    def test_same_content_same_checksum(self):
        assert compute_checksum("SELECT 1;") == compute_checksum("SELECT 1;")

    def test_different_content_different_checksum(self):
        assert compute_checksum("SELECT 1;") != compute_checksum("SELECT 2;")

    def test_returns_hex_string(self):
        result = compute_checksum("test")
        assert all(c in "0123456789abcdef" for c in result)
        assert len(result) == 32


class TestFormatDuration:
    def test_seconds_only(self):
        assert format_duration(5.5) == "5.50s"

    def test_minutes_and_seconds(self):
        assert format_duration(90.0) == "1m 30.00s"

    def test_zero(self):
        assert format_duration(0.0) == "0.00s"


class TestGetSortedMigrationFiles:
    def test_returns_sorted_files(self):
        tmpdir = tempfile.mkdtemp()
        for name in ["V3__c.sql", "V1__a.sql", "V2__b.sql"]:
            open(os.path.join(tmpdir, name), "w").write("SELECT 1;")
        result = get_sorted_migration_files(tmpdir)
        assert result == ["V1__a.sql", "V2__b.sql", "V3__c.sql"]

    def test_ignores_non_sql_files(self):
        tmpdir = tempfile.mkdtemp()
        open(os.path.join(tmpdir, "V1__a.sql"), "w").write("SELECT 1;")
        open(os.path.join(tmpdir, "README.md"), "w").write("docs")
        result = get_sorted_migration_files(tmpdir)
        assert result == ["V1__a.sql"]

    def test_empty_dir_returns_empty_list(self):
        tmpdir = tempfile.mkdtemp()
        assert get_sorted_migration_files(tmpdir) == []

    def test_missing_dir_returns_empty_list(self):
        assert get_sorted_migration_files("/nonexistent") == []


class TestSplitSqlStatements:
    def test_single_statement(self):
        result = split_sql_statements("CREATE TABLE t (id INT)")
        assert result == ["CREATE TABLE t (id INT)"]

    def test_multiple_statements(self):
        sql = "CREATE TABLE a (id INT); CREATE TABLE b (id INT);"
        result = split_sql_statements(sql)
        assert len(result) == 2

    def test_empty_input(self):
        assert split_sql_statements("") == []

    def test_whitespace_only(self):
        assert split_sql_statements("   ;   ;  ") == []


class TestMaskPassword:
    def test_masks_password(self):
        dsn = "host=localhost password=secret123 dbname=mydb"
        result = mask_password(dsn)
        assert "secret123" not in result
        assert "****" in result

    def test_no_password_unchanged(self):
        dsn = "host=localhost dbname=mydb"
        assert mask_password(dsn) == dsn
