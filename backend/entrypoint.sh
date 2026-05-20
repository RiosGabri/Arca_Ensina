#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Checking fixtures..."
python manage.py shell -c "
from apps.protocols.models import Protocol
if not Protocol.objects.filter(title='Protocolo de Manejo da Dengue').exists():
    from django.core.management import call_command
    call_command('loaddata', 'apps/protocols/fixtures/dengue_guiado.json')
    call_command('loaddata', 'apps/protocols/fixtures/sedacao_painel.json')
    print('Fixtures loaded.')
else:
    print('Fixtures already present, skipping.')
"

echo "Checking sintomas..."
python manage.py shell -c "
from apps.pacientes.models import Sintoma
if Sintoma.objects.count() == 0:
    from django.core.management import call_command
    call_command('loaddata', 'apps/pacientes/fixtures/sintomas.json')
    print('Sintomas loaded.')
else:
    print('Sintomas already present, skipping.')
"

echo "Loading medications..."
python manage.py loaddata apps/medications/infos/medications.json
echo "Medications loaded."

exec "$@"
