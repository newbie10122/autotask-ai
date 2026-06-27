from workers.shared.worker_base import log, run_forever


def document_extraction_job() -> None:
    log("document extraction placeholder: OCR intentionally out of scope for MVP")


run_forever("worker-documents", 300, document_extraction_job)

