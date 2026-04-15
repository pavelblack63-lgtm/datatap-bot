#!/bin/bash
# SSL Setup Script for DataTap Bot
# Запусти от root

DOMAIN="your-domain.com"
EMAIL="your-email@example.com"

echo "=== SSL Setup for $DOMAIN ==="

# Certbot
apt update && apt install -y certbot python3-certbot-nginx

# Generate SSL
certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email --redirect --hsts

# Auto-renewal
crontab -l > /tmp/crontab.bak
echo "0 0 * * * certbot renew --quiet --deploy-hook 'nginx -s reload'" >> /tmp/crontab.bak
crontab /tmp/crontab.bak

echo "✅ SSL ready! https://$DOMAIN"