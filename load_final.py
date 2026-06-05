import os, sys, json
os.environ['SKIP_SIGNALS'] = '1'
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'

print('Starting...', flush=True)
import django
django.setup()
print('Django setup done', flush=True)

from django.db import connection, transaction
from django.core import serializers

print('Reloading incomplete tables...', flush=True)
with connection.cursor() as cursor:
    # Truncate tables that have partial data
    cursor.execute('TRUNCATE TABLE "accounting_app_activitylog" CASCADE')
    cursor.execute('TRUNCATE TABLE "accounting_app_beneficiaryhistory" CASCADE')
print('Truncated activitylog and beneficiaryhistory', flush=True)

# Load only activitylog and beneficiaryhistory from fixture
print('Loading fixture...', flush=True)
with open('seed_data.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Get only the models we need
needed = {'accounting_app.activitylog', 'accounting_app.beneficiaryhistory'}
by_model = {}
for obj in raw_data:
    model = obj['model']
    if model in needed:
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(obj)

for model_name, objects in by_model.items():
    batch_json = json.dumps(objects)
    deserialized = list(serializers.deserialize('json', batch_json, handle_forward_references=True))
    
    BATCH = 100
    for i in range(0, len(deserialized), BATCH):
        batch = deserialized[i:i+BATCH]
        with transaction.atomic():
            for obj in batch:
                obj.save()
    print(f'  {model_name}: {len(objects)} rows', flush=True)

print('All data loaded successfully!', flush=True)
