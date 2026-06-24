"""Create the MySQL database and application user from .env configuration."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import pymysql

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_ROOT_USER = os.getenv("MYSQL_ROOT_USER", "root")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "cms_db")
MYSQL_USER = os.getenv("MYSQL_USER", "cms_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "secure_password")


def die(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def create_database_and_user() -> None:
    if not MYSQL_ROOT_PASSWORD:
        die("MYSQL_ROOT_PASSWORD is not configured in .env. Set this value and try again.")

    print(f"Connecting to MySQL server at {MYSQL_HOST}:{MYSQL_PORT} as {MYSQL_ROOT_USER}...")

    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_ROOT_USER,
            password=MYSQL_ROOT_PASSWORD,
            autocommit=True,
        )
    except Exception as exc:
        die(f"Unable to connect to MySQL server: {exc}")

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            print(f"Database '{MYSQL_DATABASE}' created or already exists.")

            cursor.execute(
                f"CREATE USER IF NOT EXISTS '{MYSQL_USER}'@'localhost' IDENTIFIED BY %s;",
                (MYSQL_PASSWORD,),
            )
            print(f"User '{MYSQL_USER}' created or already exists.")

            cursor.execute(
                f"GRANT ALL PRIVILEGES ON `{MYSQL_DATABASE}`.* TO '{MYSQL_USER}'@'localhost';"
            )
            cursor.execute("FLUSH PRIVILEGES;")
            print(f"Granted privileges to '{MYSQL_USER}' on '{MYSQL_DATABASE}'.")

    finally:
        connection.close()

    print("MySQL database and user setup is complete.")
    print("Update your .env DATABASE_URL to use the created MySQL user and database.")


if __name__ == "__main__":
    create_database_and_user()
