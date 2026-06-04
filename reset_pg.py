import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://inventory_ugek_user:0V8C4IoBtmIjFIkaRXGndlCRKIVbtYr3@dpg-d84abpj7uimc739h653g-a.ohio-postgres.render.com:5432/inventory_ugek'

import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")
    tables = [r[0] for r in cursor.fetchall()]

    tables_to_drop = [t for t in tables if t.startswith('accounting_app_') or t.startswith('system_modules_')]
    
    for t in tables_to_drop:
        cursor.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
        print(f'Dropped {t}')

print('Reset complete')
