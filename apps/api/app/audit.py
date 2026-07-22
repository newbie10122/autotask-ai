from .models import AuditAction, AuditLogEntry


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

    def list_recent(
        self,
        *,
        actor: str | None = None,
        action: AuditAction | None = None,
        outcome: str | None = None,
        target: str | None = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        action_value = action.value if action else None
        try:
            from .db import db_connection

            filters = []
            params: list[object] = []
            if actor:
                filters.append("actor = %s")
                params.append(actor)
            if action_value:
                filters.append("action = %s")
                params.append(action_value)
            if outcome:
                filters.append("outcome = %s")
                params.append(outcome)
            if target:
                filters.append("target = %s")
                params.append(target)
            where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
            params.append(limit)
            with db_connection() as conn:
                rows = conn.execute(
                    f"""
                    SELECT actor, action, target, outcome, scope, metadata, created_at
                    FROM audit_log
                    {where_clause}
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    tuple(params),
                ).fetchall()
            return [AuditLogEntry(**dict(row)) for row in rows]
        except Exception:
            pass
        entries = list(reversed(self.entries))
        if actor:
            entries = [entry for entry in entries if entry.actor == actor]
        if action:
            entries = [entry for entry in entries if entry.action == action]
        if outcome:
            entries = [entry for entry in entries if entry.outcome == outcome]
        if target:
            entries = [entry for entry in entries if entry.target == target]
        return entries[:limit]


audit_sink = InMemoryAuditSink()
