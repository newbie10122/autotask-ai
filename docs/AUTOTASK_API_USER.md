# Autotask API User Setup

Create an API-only Autotask user for this MVP. The app uses read-only Autotask REST calls and sends the required `Username`, `Secret`, and `APIIntegrationcode` headers from environment variables.

1. In Autotask, create or select an API-only security level with read permissions for companies, contacts, tickets, ticket notes, time entries, assets, and attachments.
2. Create a dedicated API user for Autotask AI.
3. Assign the API user to the API-only security level.
4. Create or select an integration vendor/tracking identifier and copy its API integration code.
5. Store credentials only in `/opt/apps/autotask-ai/.env`.

Use these `.env` keys:

```dotenv
AUTOTASK_USERNAME=
AUTOTASK_SECRET=
AUTOTASK_API_INTEGRATION_CODE=
```

MVP rules:

- Sync jobs use 500-record query pages.
- Sync state is resumable through stored resume tokens.
- API call counts are written to `autotask_api_calls`.
- Create, update, and delete operations are intentionally unavailable.

