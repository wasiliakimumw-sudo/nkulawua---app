import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

import django
django.setup()
from django.db import connection

tables = ['auth_user', 'accounting_app_beneficiary', 'accounting_app_invoice',
          'accounting_app_payment', 'accounting_app_account', 'accounting_app_village',
          'accounting_app_scheme', 'accounting_app_expense', 'accounting_app_vendor',
          'accounting_app_userprofile', 'accounting_app_activitylog']

c = connection.cursor()
for t in tables:
    try:
        c.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = c.fetchone()[0]
        print(f'{t}: {count} rows')
    except Exception as e:
        print(f'{t}: ERROR - {e}')
