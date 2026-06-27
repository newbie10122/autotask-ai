from .models import AuditLogEntry


class InMemoryAuditSink:
    def __init__(self) -> None:
        self.entries: list[AuditLogEntry] = []

    def record(self, entry: AuditLogEntry) -> AuditLogEntry:
        self.entries.append(entry)
        return entry

    def list_recent(self) -> list[AuditLogEntry]:
        return list(reversed(self.entries))


audit_sink = InMemoryAuditSink()

