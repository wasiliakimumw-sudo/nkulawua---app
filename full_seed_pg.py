import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
DB_URL = 'postgresql://inventory_ugek_user:0V8C4IoBtmIjFIkaRXGndlCRKIVbtYr3@dpg-d84abpj7uimc739h653g-a.ohio-postgres.render.com:5432/inventory_ugek'
os.environ['DATABASE_URL'] = DB_URL

import django
django.setup()

from django.db import connection
from django.core import management

print('=== Step 1: Drop all project tables & migration records ===')
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
    tables = [r[0] for r in cursor.fetchall()]
    our_tables = [t for t in tables if any(t.startswith(p) for p in ('accounting_app_', 'system_modules_', 'auth_', 'django_', 'crispy_'))]
    for t in our_tables:
        cursor.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
        print(f'  Dropped {t}')

print()
print('=== Step 2: Run migrations ===')
management.call_command('migrate', verbosity=1)

print()
print('=== Step 3: Load data ===')
management.call_command('loaddata', 'seed_data.json', verbosity=1)

print()
print('=== Done! All data seeded successfully ===')
