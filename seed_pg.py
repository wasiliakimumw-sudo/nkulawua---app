import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://inventory_ugek_user:0V8C4IoBtmIjFIkaRXGndlCRKIVbtYr3@dpg-d84abpj7uimc739h653g-a.ohio-postgres.render.com:5432/inventory_ugek'

import django
django.setup()

from django.core import management
management.call_command('loaddata', 'seed_data.json', verbosity=1)
print('Loaddata completed successfully')
