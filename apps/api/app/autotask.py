from dataclasses import dataclass


@dataclass(frozen=True)
class AutotaskHeaders:
    username: str
    secret: str
    api_integration_code: str

    def as_http_headers(self) -> dict[str, str]:
        return {
            "Username": self.username,
            "Secret": self.secret,
            "APIIntegrationcode": self.api_integration_code,
        }


class AutotaskReadOnlyClient:
    page_size = 500

    def test_connection(self) -> dict:
        return {
            "ok": False,
            "status": "placeholder",
            "message": "Autotask connection test is not wired in this MVP foundation.",
        }

    def query_tickets_page(self, resume_token: str | None = None) -> dict:
        return {"records": [], "next_resume_token": resume_token, "page_size": self.page_size}

    def create_ticket(self, *_args, **_kwargs):
        raise NotImplementedError("Autotask write calls are disabled in the MVP.")

    def update_ticket(self, *_args, **_kwargs):
        raise NotImplementedError("Autotask write calls are disabled in the MVP.")

    def delete_ticket(self, *_args, **_kwargs):
        raise NotImplementedError("Autotask write calls are disabled in the MVP.")

