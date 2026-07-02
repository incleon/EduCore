"""Small, supported command line interface for database operations."""

import argparse

from app.database.seed import (
    clean_database_keep_admin,
    seed_demo_data,
    seed_system_data,
)
from app.database.session import SessionLocal, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="EduCore database operations")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "init-db",
        help="create missing tables and required roles, permissions, and admin",
    )
    subcommands.add_parser(
        "seed-demo",
        help="replace business data with the complete demonstration dataset",
    )
    subcommands.add_parser(
        "clean-demo",
        help="remove business data while preserving the admin and access metadata",
    )
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        if args.command == "init-db":
            seed_system_data(db)
        elif args.command == "seed-demo":
            seed_demo_data(db)
        else:
            clean_database_keep_admin(db)


if __name__ == "__main__":
    main()
