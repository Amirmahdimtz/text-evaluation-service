"""Run committed migrations on a separately provisioned *local test* PostgreSQL only."""
from __future__ import annotations

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config

from src.infrastructure.context.sql_db.psql_dbcontext import get_test_database_url

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("current", "upgrade"))
    args = parser.parse_args()
    # Fail before running Alembic, even when action=current.
    get_test_database_url()
    config = Config()
    config.set_main_option("script_location", str(ROOT / "src/infrastructure/alembic"))
    if args.action == "current":
        command.current(config, verbose=True)
    else:
        command.upgrade(config, "head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
