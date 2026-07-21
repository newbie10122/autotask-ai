from .models import AuditLogEntry


class InMemoryAuditSink:
    def __init__(self) -> None:
        self.entries: list[AuditLogEntry] = []

    def record(self, entry: AuditLogEntry) -> AuditLogEntry:
        self.entries.append(entry)
        try:
            from psycopg.types.json import Jsonb

            from .db import db_connection

            with db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_log(actor, action, target, outcome, scope, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        entry.actor,
                        entry.action.value,
                        entry.target,
                        entry.outcome,
                        Jsonb(entry.scope),
                        Jsonb(entry.metadata),
                        entry.created_at,
                    ),
                )
        except Exception:
            pass
        return entry

    def list_recent(self) -> list[AuditLogEntry]:
        try:
            from .db import db_connection

            with db_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT actor, action, target, outcome, scope, metadata, created_at
                    FROM audit_log
                    ORDER BY created_at DESC, id DESC
                    LIMIT 100
                    """
                ).fetchall()
            return [AuditLogEntry(**dict(row)) for row in rows]
        except Exception:
            pass
        return list(reversed(self.entries))


audit_sink = InMemoryAuditSink()
