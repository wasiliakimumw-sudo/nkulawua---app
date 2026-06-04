import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://inventory_ugek_user:0V8C4IoBtmIjFIkaRXGndlCRKIVbtYr3@dpg-d84abpj7uimc739h653g-a.ohio-postgres.render.com:5432/inventory_ugek'

import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = cursor.fetchone()[0]
        print(f'{t}: {count} rows')
