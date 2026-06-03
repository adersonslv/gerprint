#!/bin/bash
set -e

echo "=== GerPrint — iniciando ==="

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear 2>/dev/null || python manage.py collectstatic --noinput

# Cria superusuário na primeira execução se as variáveis estiverem definidas
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "${DJANGO_SUPERUSER_EMAIL:-admin@gerprint.local}" \
        2>/dev/null || true
fi

echo "Acesse: http://localhost:${PORT:-8000}"
echo "Admin:  http://localhost:${PORT:-8000}/admin"

exec python manage.py runserver 0.0.0.0:${PORT:-8000}
