# Nginx HTTP Preview

Autotask AI can be exposed through a dedicated HTTP-only Nginx preview site on trusted internal or VPN networks.

## Paths

- Site file: `/etc/nginx/sites-available/autotask-ai`
- Enabled symlink: `/etc/nginx/sites-enabled/autotask-ai`
- Basic Auth file: `/etc/nginx/.helix-preview-auth`

## HTTP-Only Warning

This pass does not configure SSL. Basic Auth credentials are not encrypted without HTTPS. Use this HTTP-only preview only on trusted, internal, or VPN-protected networks until SSL is added.

Do not run certbot for this pass.

## Backends

- Web UI: `127.0.0.1:3010`
- API: `127.0.0.1:5110`

PostgreSQL and Ollama stay private and are not exposed through Nginx.

## Install

Use the helper script:

```bash
sudo bash scripts/install-nginx-http-preview.sh autotask-ai.compuone.local
```

The script verifies `/etc/nginx/.helix-preview-auth`, writes the dedicated site, enables it, runs `nginx -t`, reloads Nginx, and prints safe test commands.

## Health Tests

Local API:

```bash
curl -sS http://127.0.0.1:5110/health
```

Nginx preview, unauthenticated:

```bash
curl -I -H "Host: autotask-ai.compuone.local" http://127.0.0.1/
curl -I -H "Host: autotask-ai.compuone.local" http://127.0.0.1/api/health
```

`401 Unauthorized` is expected because Basic Auth is enabled. `404` and `502` are not acceptable.

## SSL Later

Add certbot and HTTPS later when hostname and DNS are final.
