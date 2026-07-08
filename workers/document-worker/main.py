from workers.shared.worker_base import log, run_forever
from app.documents import create_documents_from_tickets


def document_extraction_job() -> None:
    result = create_documents_from_tickets(limit=500)
    log(f"document creation completed: {result}")


run_forever("worker-documents", 300, document_extraction_job)
