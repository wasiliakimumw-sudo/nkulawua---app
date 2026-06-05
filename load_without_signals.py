import os
os.environ['SKIP_SIGNALS'] = '1'
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'

import django
django.setup()

from django.db import connection
from django.core import management

print('Truncating tables...')
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name LIKE 'accounting_app_%'")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f'TRUNCATE TABLE "{t}" CASCADE')
    cursor.execute('TRUNCATE TABLE "auth_user" CASCADE')
    cursor.execute('TRUNCATE TABLE "auth_user_groups" CASCADE')
    cursor.execute('TRUNCATE TABLE "auth_user_user_permissions" CASCADE')
print('Truncated.')

print('Loading data (signals disabled)...')
management.call_command('loaddata', 'seed_data.json', verbosity=1)
print('Done!')
