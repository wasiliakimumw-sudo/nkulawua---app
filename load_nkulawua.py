"""Load fixture into PostgreSQL using raw psycopg2 for speed, bypassing Django ORM/signals."""
import os, json, csv, io
os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_project.settings'
os.environ['DATABASE_URL'] = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'

import django
django.setup()

import dj_database_url
from django.conf import settings
import psycopg2
from psycopg2.extras import execute_values

# Parse DB config
db_config = dj_database_url.parse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(
    host=db_config['HOST'],
    port=db_config['PORT'],
    dbname=db_config['NAME'],
    user=db_config['USER'],
    password=db_config['PASSWORD'],
)
conn.autocommit = True
cur = conn.cursor()

print('Truncating tables...')
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name LIKE 'accounting_app_%'")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    cur.execute(f'TRUNCATE TABLE "{t}" CASCADE')
cur.execute('TRUNCATE TABLE "auth_user" CASCADE')
cur.execute('TRUNCATE TABLE "django_session" CASCADE')
print('Truncated')

# Read fixture
with open('seed_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Group objects by model
from collections import OrderedDict
by_model = OrderedDict()
for obj_data in data:
    model = obj_data['model']
    if model not in by_model:
        by_model[model] = []
    by_model[model].append(obj_data)

# Map model names to table names
model_table_map = {}
from django.apps import apps
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        model_table_map[f'{app_config.label}.{model._meta.model_name}'] = model._meta.db_table

# Get column info for each table
table_columns = {}
cur.execute("SELECT table_name, column_name, ordinal_position FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position")
for t, c, _ in cur.fetchall():
    if t not in table_columns:
        table_columns[t] = []
    table_columns[t].append(c)

INSERT_BATCH = 500
total_inserted = 0

for model_name, objects in by_model.items():
    table = model_table_map.get(model_name)
    if not table:
        print(f'  SKIP {model_name}: no table mapping')
        continue
    
    cols = table_columns.get(table, [])
    if not cols:
        print(f'  SKIP {table}: no columns found')
        continue
    
    # Filter out 'id' from columns since we're inserting with PK
    # We'll include all columns from the fixture data
    pk_col = 'id'
    
    print(f'  Loading {len(objects)} rows into {table}...')
    
    for i in range(0, len(objects), INSERT_BATCH):
        batch = objects[i:i + INSERT_BATCH]
        rows = []
        
        for obj_data in batch:
            fields = obj_data.get('fields', {})
            pk = obj_data.get('pk')
            
            # Build row matching column order
            row = []
            for col in cols:
                if col == pk_col:
                    row.append(pk)
                elif col in fields:
                    val = fields[col]
                    # Handle None vs null
                    if val is None:
                        row.append(None)
                    else:
                        row.append(val)
                else:
                    row.append(None)
            rows.append(row)
        
        # Build INSERT query
        col_names = ', '.join(f'"{c}"' for c in cols)
        placeholders = ', '.join(['%s'] * len(cols))
        query = f'INSERT INTO "{table}" ({col_names}) VALUES %s ON CONFLICT DO NOTHING'
        
        try:
            execute_values(cur, query, rows, template=None, page_size=INSERT_BATCH)
            conn.commit()
            total_inserted += len(rows)
        except Exception as e:
            conn.rollback()
            print(f'    Error at batch {i}: {e}')
            # Try one by one
            for row in rows:
                try:
                    execute_values(cur, query, [row], template=None, page_size=1)
                    conn.commit()
                    total_inserted += 1
                except Exception as e2:
                    conn.rollback()
                    print(f'    Skipping row: {e2}')
    
    print(f'    Done: {len(objects)} rows')

cur.close()
conn.close()
print(f'\nTotal: {total_inserted} objects inserted')
