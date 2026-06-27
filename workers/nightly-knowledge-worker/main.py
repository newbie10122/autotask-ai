from workers.shared.worker_base import log, run_forever


def nightly_repair_and_summarization_job() -> None:
    log("nightly repair/summarization placeholder: curated memory remains pending until approved")


run_forever("worker-nightly", 3600, nightly_repair_and_summarization_job)

