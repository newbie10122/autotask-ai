from __future__ import annotations

import argparse
import os
from typing import Any

from psycopg.types.json import Jsonb

from .db import db_connection
from .models import Role
from .security import hash_password


VALID_ROLES = {role.value for role in Role}
MIN_BOOTSTRAP_PASSWORD_LENGTH = 16


def normalize_roles(roles: list[str]) -> list[str]:
    unique_roles = sorted(set(roles))
    if not unique_roles:
        raise ValueError("At least one role is required.")
    invalid_roles = [role for role in unique_roles if role not in VALID_ROLES]
    if invalid_roles:
        raise ValueError(f"Unsupported role(s): {', '.join(invalid_roles)}.")
    return unique_roles


def upsert_app_user(username: str, password: str, roles: list[str], disabled: bool = False) -> dict[str, Any]:
    clean_username = username.strip()
    if not clean_username:
        raise ValueError("Username is required.")
    if len(password) < MIN_BOOTSTRAP_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_BOOTSTRAP_PASSWORD_LENGTH} characters.")
    normalized_roles = normalize_roles(roles)
    password_hash = hash_password(password)
    with db_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO app_users (username, password_hash, roles, disabled)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username)
            DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                roles = EXCLUDED.roles,
                disabled = EXCLUDED.disabled,
                updated_at = now()
            RETURNING username, roles, disabled
            """,
            (clean_username, password_hash, Jsonb(normalized_roles), disabled),
        ).fetchone()
    return {"username": row["username"], "roles": row["roles"], "disabled": row["disabled"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a local Autotask AI app user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", action="append", dest="roles")
    parser.add_argument("--password-env", default="BOOTSTRAP_APP_PASSWORD")
    parser.add_argument("--disabled", action="store_true")
    args = parser.parse_args()

    password = os.environ.get(args.password_env)
    if not password:
        raise SystemExit(f"Set {args.password_env} before running this command.")
    user = upsert_app_user(args.username, password, args.roles or [Role.admin.value], disabled=args.disabled)
    print(f"Updated app user {user['username']} with roles: {', '.join(user['roles'])}; disabled={user['disabled']}")


if __name__ == "__main__":
    main()
