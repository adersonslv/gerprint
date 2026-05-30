#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "=== GerPrint - Sistema de Gestão de Impressoras ==="
echo "Acesse: http://127.0.0.1:8000"
echo "Admin:  http://127.0.0.1:8000/admin  (usuário: admin / senha: admin123)"
echo ""
python manage.py runserver
