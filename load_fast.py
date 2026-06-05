import os, sys, json
os.environ['SKIP_SIGNALS'] = '1'
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'

print('Starting...', flush=True)
import django
django.setup()
print('Django setup done', flush=True)

from django.db import connection
from django.core import serializers

print('Truncating tables...', flush=True)
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name LIKE 'accounting_app_%'")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f'TRUNCATE TABLE "{t}" CASCADE')
    cursor.execute('TRUNCATE TABLE "auth_user" CASCADE')
    cursor.execute('TRUNCATE TABLE "auth_user_groups" CASCADE')
    cursor.execute('TRUNCATE TABLE "auth_user_user_permissions" CASCADE')
print(f'Truncated', flush=True)

# Load fixture, grouping by model to respect FK order
print('Loading fixture...', flush=True)
with open('seed_data.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Define load order (parents first)
LOAD_ORDER = [
    'auth.user',
    'accounting_app.scheme',
    'accounting_app.village',
    'accounting_app.account',
    'accounting_app.taxrate',
    'accounting_app.galleryimage',
    'accounting_app.landingpagesettings',
    'accounting_app.boardoftrustees',
    'accounting_app.generalassemblymember',
    'accounting_app.service',
    'accounting_app.beneficiary',
    'accounting_app.vendor',
    'accounting_app.employee',
    'accounting_app.budget',
    'accounting_app.beneficiaryhistory',
    'accounting_app.beneficiarystatuslog',
    'accounting_app.invoice',
    'accounting_app.invoiceitem',
    'accounting_app.expense',
    'accounting_app.expenseitem',
    'accounting_app.openingbalance',
    'accounting_app.balancehistory',
    'accounting_app.budgetline',
    'accounting_app.employeesalary',
    'accounting_app.payment',
    'accounting_app.communicationlog',
    'accounting_app.journalentry',
    'accounting_app.journalentryline',
    'accounting_app.report',
    'accounting_app.activitylog',
    'accounting_app.usermessage',
    'accounting_app.usercall',
    'accounting_app.loginsession',
    'accounting_app.userprofile',
    'accounting_app.deletedrecord',
    'accounting_app.datamigrationlog',
    'accounting_app.systemupdatelog',
    'accounting_app.systemversion',
    'accounting_app.villagepopulation',
    'accounting_app.yearendrollover',
]

# Group objects by model
by_model = {}
for obj in raw_data:
    model = obj['model']
    if model not in by_model:
        by_model[model] = []
    by_model[model].append(obj)

# Load in order
total = 0
for model_name in LOAD_ORDER:
    objects = by_model.pop(model_name, [])
    if not objects:
        continue
    
    batch_json = json.dumps(objects)
    deserialized = list(serializers.deserialize('json', batch_json, handle_forward_references=True))
    
    BATCH = 50
    for i in range(0, len(deserialized), BATCH):
        batch = deserialized[i:i+BATCH]
        from django.db import transaction
        with transaction.atomic():
            for obj in batch:
                obj.save()
        total += len(batch)
    
    print(f'  {model_name}: {len(objects)} rows', flush=True)

# Any remaining models not in LOAD_ORDER
for model_name, objects in by_model.items():
    batch_json = json.dumps(objects)
    deserialized = list(serializers.deserialize('json', batch_json, handle_forward_references=True))
    BATCH = 50
    for i in range(0, len(deserialized), BATCH):
        batch = deserialized[i:i+BATCH]
        from django.db import transaction
        with transaction.atomic():
            for obj in batch:
                obj.save()
        total += len(batch)
    print(f'  {model_name}: {len(objects)} rows (unordered)', flush=True)

print(f'Done! Loaded {total} objects total', flush=True)
