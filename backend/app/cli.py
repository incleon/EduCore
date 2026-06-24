"""Supported command-line entry point for routine backend operations."""

import argparse

from app.database.seed import seed_database
from app.database.session import SessionLocal, init_db


def initialize_database(seed: bool = True) -> None:
    init_db()
    if seed:
        with SessionLocal() as db:
            seed_database(db)


def main() -> None:
    parser = argparse.ArgumentParser(description="EduCore backend operations")
    subcommands = parser.add_subparsers(dest="command", required=True)
    init_parser = subcommands.add_parser("init-db", help="Create tables and seed base data")
    init_parser.add_argument("--no-seed", action="store_true", help="Create tables only")
    args = parser.parse_args()

    if args.command == "init-db":
        initialize_database(seed=not args.no_seed)


if __name__ == "__main__":
    main()
