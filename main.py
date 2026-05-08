#!/usr/bin/env python3
"""
main.py

Entry point for the Database Migration Runner.
Validates migrations, runs them, and sends a Slack notification.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from src.db.connection import DatabaseConnection
from src.logger.logger import get_logger
from src.notifier.slack_notifier import MigrationNotification, SlackNotifier
from src.runner.migration_runner import MigrationRunner
from src.validator.migration_validator import MigrationValidator

logger = get_logger("main")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")


def main() -> int:
    environment = os.getenv("ENVIRONMENT", "staging")
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    logger.info("=== Database Migration Runner ===")
    logger.info("Environment : %s", environment)
    logger.info("Dry Run     : %s", dry_run)
    logger.info("Migrations  : %s", MIGRATIONS_DIR)

    # --- Step 1: Validate migrations ---
    logger.info("--- Step 1: Validating migrations ---")
    validator = MigrationValidator(MIGRATIONS_DIR)
    validation_result = validator.run_all()

    if not validation_result.valid:
        logger.error("Validation failed. Aborting migration.\n%s", validation_result.summary())
        notifier = SlackNotifier()
        notifier.send(
            MigrationNotification(
                status="failure",
                environment=environment,
                migrations_applied=0,
                migrations_list=[],
                error_message="Validation failed: " + "; ".join(validation_result.errors),
            )
        )
        return 1

    if validation_result.warnings:
        for warning in validation_result.warnings:
            logger.warning("Validation warning: %s", warning)

    # --- Step 2: Run migrations ---
    logger.info("--- Step 2: Running migrations ---")
    db = DatabaseConnection()
    try:
        db.connect()
    except ConnectionError as exc:
        logger.error("Cannot connect to database: %s", exc)
        SlackNotifier().send(
            MigrationNotification(
                status="failure",
                environment=environment,
                migrations_applied=0,
                migrations_list=[],
                error_message=str(exc),
            )
        )
        return 1

    runner = MigrationRunner(
        db_connection=db,
        migrations_dir=MIGRATIONS_DIR,
        environment=environment,
        dry_run=dry_run,
    )
    result = runner.run()

    # --- Step 3: Send Slack notification ---
    logger.info("--- Step 3: Sending Slack notification ---")
    notifier = SlackNotifier()

    applied_names = [r.filename for r in result.applied]

    notifier.send(
        MigrationNotification(
            status="success" if result.success else "failure",
            environment=environment,
            migrations_applied=len(result.applied),
            migrations_list=applied_names,
            error_message=result.error_message,
            migration_file=result.failed_file,
            duration_seconds=result.total_duration,
            branch=result.branch,
            commit_sha=result.commit_sha,
        )
    )

    if result.success:
        logger.info(
            "Migration run completed successfully. Applied: %d, Skipped: %d.",
            len(result.applied),
            len(result.skipped),
        )
        return 0
    else:
        logger.error(
            "Migration run failed on: %s. Error: %s",
            result.failed_file,
            result.error_message,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
