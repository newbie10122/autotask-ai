CREATE INDEX IF NOT EXISTS autotask_ticket_notes_ticket_id_idx
    ON autotask_ticket_notes(ticket_id, created_at_autotask NULLS LAST, autotask_id);

CREATE INDEX IF NOT EXISTS autotask_ticket_notes_autotask_ticket_id_idx
    ON autotask_ticket_notes(autotask_ticket_id, created_at_autotask NULLS LAST, autotask_id);

CREATE INDEX IF NOT EXISTS autotask_tickets_autotask_id_idx
    ON autotask_tickets(autotask_id);
