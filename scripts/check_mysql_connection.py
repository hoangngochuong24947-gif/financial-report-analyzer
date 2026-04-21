"""Quick MySQL connectivity check for the local development environment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mysql.connector
from mysql.connector import Error

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify MySQL connectivity and optionally create the target database.",
    )
    parser.add_argument("--host", default=settings.mysql_host)
    parser.add_argument("--port", type=int, default=settings.mysql_port)
    parser.add_argument("--user", default=settings.mysql_user)
    parser.add_argument("--password", default=settings.mysql_password)
    parser.add_argument("--database", default=settings.mysql_database)
    parser.add_argument(
        "--create-db",
        action="store_true",
        help="Create the database if it does not exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = None
    try:
        conn = mysql.connector.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
        )
        with conn.cursor() as cursor:
            if args.create_db:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{args.database}` "
                    "DEFAULT CHARACTER SET utf8mb4"
                )
                print(f"[ok] database ensured: {args.database}")

            cursor.execute(f"USE `{args.database}`")
            cursor.execute("SELECT VERSION(), DATABASE()")
            version, current_db = cursor.fetchone()

        print("[ok] MySQL connection succeeded")
        print(f"host={args.host} port={args.port} user={args.user}")
        print(f"database={current_db}")
        print(f"version={version}")
        return 0
    except Error as exc:
        print("[error] MySQL connection failed")
        print(str(exc))
        return 1
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
