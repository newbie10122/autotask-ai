#!/usr/bin/env bash
set -euo pipefail

HOSTNAME="${1:-autotask-ai.compuone.local}"
SITE_AVAILABLE="/etc/nginx/sites-available/autotask-ai"
SITE_ENABLED="/etc/nginx/sites-enabled/autotask-ai"
AUTH_FILE="/etc/nginx/.helix-preview-auth"

if [[ ! -f "$AUTH_FILE" ]]; then
  echo "Missing /etc/nginx/.helix-preview-auth. Create it first with htpasswd or provide the correct Basic Auth file path."
  exit 1
fi

sudo tee "$SITE_AVAILABLE" >/dev/null <<NGINX
server {
    listen 80;
    server_name ${HOSTNAME};

    auth_basic "Autotask AI";
    auth_basic_user_file /etc/nginx/.helix-preview-auth;

    add_header X-Robots-Tag "noindex, nofollow, noarchive, nosnippet" always;

    location = /robots.txt {
        return 200 "User-agent: *\nDisallow: /\n";
        add_header Content-Type text/plain;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5110/api/;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:3010;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX

sudo ln -sf "$SITE_AVAILABLE" "$SITE_ENABLED"
sudo nginx -t
sudo systemctl reload nginx

echo "Installed HTTP-only Autotask AI Nginx preview for ${HOSTNAME}."
echo "Test commands:"
echo "curl -I -H \"Host: ${HOSTNAME}\" http://127.0.0.1/"
echo "curl -I -H \"Host: ${HOSTNAME}\" http://127.0.0.1/api/health"
