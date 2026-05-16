#!/bin/bash
# Script de déploiement — à lancer sur ct-api (/srv/api/)
# Usage: ./deploy.sh

set -e

echo "Mise à jour du code..."
git pull origin main

echo "Installation des dépendances Python..."
/usr/local/bin/uv sync

echo "Migrations base de données..."
/usr/local/bin/uv run alembic upgrade head

echo "Build du panel admin..."
cd admin-src
npm ci
npm run build
cd ..

echo "Redémarrage du service..."
systemctl restart multisite-api

echo "Statut :"
systemctl status multisite-api --no-pager
