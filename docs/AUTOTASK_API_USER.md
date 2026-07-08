# Autotask API User Setup

Create an API-only Autotask user for this MVP. The app uses read-only Autotask REST calls and sends the required `Username`, `Secret`, and `APIIntegrationcode` headers from environment variables.

1. In Autotask, create or select an API-only security level with read permissions for companies, contacts, tickets, ticket notes, time entries, assets, and attachments.
2. Create a dedicated API user for Autotask AI.
3. Assign the API user to the API-only security level.
4. Create or select an integration vendor/tracking identifier and copy its API integration code.
5. Store credentials only in `/opt/apps/autotask-ai/.env`.

Use these `.env` keys:

```dotenv
AUTOTASK_BASE_URL=https://webservices15.autotask.net/ATServicesRest
AUTOTASK_USERNAME=
AUTOTASK_SECRET=
AUTOTASK_API_INTEGRATION_CODE=
AUTOTASK_PAGE_SIZE=500
AUTOTASK_SYNC_BATCH_LIMIT=500
```

MVP rules:

- Sync jobs cap query pages at 500 records.
- Sync state is resumable through `id > last_seen_id` checkpoints.
- API call details are written to `autotask_api_calls`, including endpoint, method, status, duration, success, and errors.
- Create, update, and delete operations are intentionally unavailable.

Validation endpoints:

- `GET /api/autotask/threshold`
- `POST /api/autotask/test/companies`
- `POST /api/autotask/test/tickets`
- `POST /api/autotask/test/ticket-notes`
