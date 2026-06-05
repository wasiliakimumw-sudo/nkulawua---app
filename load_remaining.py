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

# Check which tables are empty
print('Checking tables...', flush=True)
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name LIKE 'accounting_app_%' ORDER BY table_name")
    all_tables = [r[0] for r in cursor.fetchall()]
    empty_tables = []
    for t in all_tables:
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        if cursor.fetchone()[0] == 0:
            empty_tables.append(t)
    # Also check auth_user
    cursor.execute('SELECT COUNT(*) FROM "auth_user"')
    auth_count = cursor.fetchone()[0]

print(f'Empty tables: {empty_tables}', flush=True)
print(f'Auth users: {auth_count}', flush=True)

# Load fixture, only load data for empty tables
print('Loading fixture...', flush=True)
with open('seed_data.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Map model name to table name
model_table_mapping = {
    'auth.user': 'auth_user',
    'accounting_app.account': 'accounting_app_account',
    'accounting_app.activitylog': 'accounting_app_activitylog',
    'accounting_app.balancehistory': 'accounting_app_balancehistory',
    'accounting_app.beneficiaryhistory': 'accounting_app_beneficiaryhistory',
    'accounting_app.beneficiarystatuslog': 'accounting_app_beneficiarystatuslog',
    'accounting_app.budgetline': 'accounting_app_budgetline',
    'accounting_app.communicationlog': 'accounting_app_communicationlog',
    'accounting_app.datamigrationlog': 'accounting_app_datamigrationlog',
    'accounting_app.deletedrecord': 'accounting_app_deletedrecord',
    'accounting_app.employeesalary': 'accounting_app_employeesalary',
    'accounting_app.expenseitem': 'accounting_app_expenseitem',
    'accounting_app.expense': 'accounting_app_expense',
    'accounting_app.galleryimage': 'accounting_app_galleryimage',
    'accounting_app.invoiceitem': 'accounting_app_invoiceitem',
    'accounting_app.invoice': 'accounting_app_invoice',
    'accounting_app.journalentryline': 'accounting_app_journalentryline',
    'accounting_app.journalentry': 'accounting_app_journalentry',
    'accounting_app.loginsession': 'accounting_app_loginsession',
    'accounting_app.openingbalance': 'accounting_app_openingbalance',
    'accounting_app.payment': 'accounting_app_payment',
    'accounting_app.report': 'accounting_app_report',
    'accounting_app.service': 'accounting_app_service',
    'accounting_app.systemupdatelog': 'accounting_app_systemupdatelog',
    'accounting_app.systemversion': 'accounting_app_systemversion',
    'accounting_app.taxrate': 'accounting_app_taxrate',
    'accounting_app.usercall': 'accounting_app_usercall',
    'accounting_app.usermessage': 'accounting_app_usermessage',
    'accounting_app.userprofile': 'accounting_app_userprofile',
    'accounting_app.villagepopulation': 'accounting_app_villagepopulation',
    'accounting_app.yearendrollover': 'accounting_app_yearendrollover',
}

# Models to skip (already have data and need them loaded first)
if auth_count > 0:
    skip_models = {'auth.user'}
else:
    skip_models = set()

# Tables that have data already - skip those models
for model_name, table_name in model_table_mapping.items():
    if table_name not in empty_tables:
        skip_models.add(model_name)

print(f'Skipping models with existing data: {skip_models}', flush=True)

# Group objects by model
by_model = {}
for obj in raw_data:
    model = obj['model']
    if model in skip_models:
        continue
    if model not in by_model:
        by_model[model] = []
    by_model[model].append(obj)

# Load in dependency order
LOAD_ORDER = [
    'auth.user',  # already loaded, will be skipped
    'accounting_app.taxrate',
    'accounting_app.galleryimage',
    'accounting_app.service',
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

total = 0
for model_name in LOAD_ORDER:
    objects = by_model.pop(model_name, [])
    if not objects:
        continue
    
    batch_json = json.dumps(objects)
    deserialized = list(serializers.deserialize('json', batch_json, handle_forward_references=True))
    
    BATCH = 50
    from django.db import transaction
    for i in range(0, len(deserialized), BATCH):
        batch = deserialized[i:i+BATCH]
        with transaction.atomic():
            for obj in batch:
                obj.save()
        total += len(batch)
    
    print(f'  {model_name}: {len(objects)} rows', flush=True)

# Any remaining models
for model_name, objects in by_model.items():
    batch_json = json.dumps(objects)
    deserialized = list(serializers.deserialize('json', batch_json, handle_forward_references=True))
    BATCH = 50
    from django.db import transaction
    for i in range(0, len(deserialized), BATCH):
        batch = deserialized[i:i+BATCH]
        with transaction.atomic():
            for obj in batch:
                obj.save()
        total += len(batch)
    print(f'  {model_name}: {len(objects)} rows (unordered)', flush=True)

print(f'Done! Loaded {total} additional objects', flush=True)
