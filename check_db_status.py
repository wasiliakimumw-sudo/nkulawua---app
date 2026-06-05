import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'

import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name LIKE 'accounting_app_%' OR table_name IN ('auth_user', 'django_session') ORDER BY table_name")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = cursor.fetchone()[0]
        print(f'{t}: {count} rows')
