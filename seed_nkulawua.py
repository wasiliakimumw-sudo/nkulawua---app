import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
DB_URL = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'
os.environ['DATABASE_URL'] = DB_URL

import django
django.setup()

from django.db import connection
from django.core import management

print('=== Step 1: Run migrations ===')
management.call_command('migrate', verbosity=1)

print()
print('=== Step 2: Dump data from SQLite ===')
import subprocess, sys
dump_env = os.environ.copy()
dump_env.pop('DATABASE_URL', None)
result = subprocess.run(
    [sys.executable, '-X', 'utf8', 'manage.py', 'dumpdata',
     '--exclude', 'admin.logentry',
     '--exclude', 'contenttypes',
     '--exclude', 'auth.permission',
     '--exclude', 'accounting_app.userprofile',
     '--natural-foreign', '--natural-primary'],
    capture_output=True, text=True, cwd=r'D:\Mantchombe websites\nkula_wua-main',
    env=dump_env
)
with open('seed_data.json', 'w', encoding='utf-8') as f:
    f.write(result.stdout)
print(f'Dumped {len(result.stdout)} chars ({result.stderr.strip() if result.stderr else "no errors"})')

print()
print('=== Step 3: Clear auto-created data from post_migrate ===')
with connection.cursor() as cursor:
    cursor.execute('TRUNCATE TABLE "accounting_app_account" CASCADE')
    cursor.execute('TRUNCATE TABLE "accounting_app_activitylog" CASCADE')
print('  Truncated account and activitylog tables')

print()
print('=== Step 4: Load data (UserProfile auto-created by signals) ===')
management.call_command('loaddata', 'seed_data.json', verbosity=1)

print()
print('=== Done! Database seeded successfully ===')
