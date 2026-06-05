import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'

import django
django.setup()
from django.db import connection

c = connection.cursor()

tables = ['auth_user', 'accounting_app_beneficiary', 'accounting_app_invoice',
          'accounting_app_payment', 'accounting_app_account', 'accounting_app_village',
          'accounting_app_scheme', 'accounting_app_expense', 'accounting_app_vendor',
          'accounting_app_userprofile', 'accounting_app_activitylog',
          'accounting_app_balancehistory', 'django_session']

for t in tables:
    try:
        c.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = c.fetchone()[0]
        print(f'{t}: {count} rows')
    except Exception as e:
        print(f'{t}: ERROR - {e}')
