# DB Migration Runner

A CI/CD pipeline tool that applies PostgreSQL schema migrations to a staging
environment and reports the result to Slack.

---

## Features

- Validates migration files before execution (naming, duplicates, empty files, dangerous statements)
- Tracks applied migrations in a `schema_migrations` table to prevent re-runs
- Rolls back the current transaction on failure
- Sends structured success/failure notifications to Slack
- Generates a JSON report saved to `reports/migration_report.json`
- Dry-run mode for safe preview of pending migrations
- GitHub Actions workflow included

---

## Project Structure

```
db-migration-runner/
|-- .github/
|   `-- workflows/
|       `-- migrate.yml          # CI/CD pipeline
|-- migrations/
|   |-- V1__create_users_table.sql
|   |-- V2__add_user_profiles_table.sql
|   `-- V3__create_orders_table.sql
|-- src/
|   |-- runner/
|   |   `-- migration_runner.py  # Core execution logic
|   |-- db/
|   |   |-- connection.py        # DB connection with retry
|   |   `-- setup_staging.py     # Start/stop Docker DB
|   |-- validator/
|   |   `-- migration_validator.py
|   |-- notifier/
|   |   `-- slack_notifier.py
|   |-- logger/
|   |   `-- logger.py
|   `-- utils/
|       `-- helpers.py
|-- docker/
|   `-- docker-compose.yml       # Staging PostgreSQL
|-- tests/
|   |-- test_validator.py
|   |-- test_helpers.py
|   `-- test_notifier.py
|-- main.py                      # Entry point
|-- config.yaml
|-- requirements.txt
`-- .env.example
```

---

## Setup

### 1. Clone and install dependencies

```bash

cd db-migration-runner
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in DB_PASSWORD and SLACK_WEBHOOK_URL
```

Required variables:

| Variable          | Description                         | Default        |
|-------------------|-------------------------------------|----------------|
| DB_HOST           | PostgreSQL host                     | localhost      |
| DB_PORT           | PostgreSQL port                     | 5432           |
| DB_NAME           | Database name                       | staging_db     |
| DB_USER           | Database user                       | postgres       |
| DB_PASSWORD       | Database password                   | (required)     |
| SLACK_WEBHOOK_URL | Slack incoming webhook URL          | (optional)     |
| ENVIRONMENT       | Environment label in notifications  | staging        |
| DRY_RUN           | Preview without applying changes    | false          |

### 3. Start the staging database

```bash
docker compose -f docker/docker-compose.yml up -d
```

---

## Running Migrations

```bash
python main.py
```

### Dry-run mode

```bash
DRY_RUN=true python main.py
```

---

## Adding a New Migration

Create a file in the `migrations/` directory following the naming convention:

```
V<version>__<description>.sql
```

Examples:
- `V4__add_payments_table.sql`
- `V5__add_email_index.sql`

Version numbers must be unique and sequential. The runner sorts files
numerically by version before applying them.

---

## Validation Rules

The validator checks all migration files before any SQL is executed.

| Check                    | Result on failure |
|--------------------------|-------------------|
| Naming convention        | Error             |
| Duplicate version number | Error             |
| Empty file               | Error             |
| DROP DATABASE/SCHEMA     | Warning           |
| TRUNCATE statement       | Warning           |
| Non-sequential versions  | Warning           |

Errors abort the run. Warnings are logged but do not stop execution.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

34 tests covering the validator, helpers, and Slack notifier.

---

## GitHub Actions

The workflow in `.github/workflows/migrate.yml` runs automatically on:

- Push to `main` or `develop`
- Pull requests targeting `main`
- Manual trigger (with optional `dry_run` input)

### Required GitHub Secrets

| Secret            | Description                  |
|-------------------|------------------------------|
| DB_PASSWORD       | PostgreSQL password           |
| SLACK_WEBHOOK_URL | Slack incoming webhook URL    |

---

## Slack Notifications

Success message includes:
- Environment, branch, commit SHA
- Number of migrations applied
- List of applied migration filenames
- Total run duration

Failure message includes:
- Environment, branch, commit SHA
- Name of the failed migration file
- Error message
- Prompt to check the logs

---

## Reports

After every run, a JSON report is written to `reports/migration_report.json`:

```json
{
  "success": true,
  "environment": "staging",
  "branch": "main",
  "commit_sha": "abc1234...",
  "total_duration_seconds": 0.842,
  "applied_count": 3,
  "skipped_count": 0,
  "applied": [...],
  "skipped": [],
  "failed_file": null,
  "error_message": null
}
```
