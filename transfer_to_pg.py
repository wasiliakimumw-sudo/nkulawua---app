"""Direct data transfer SQLite -> PostgreSQL, bypassing Django ORM entirely."""
import sqlite3, psycopg2, json
from psycopg2.extras import execute_values
from collections import OrderedDict

PG_URL = 'postgresql://nkulawua_user:K8SyA8VYJvUMo8f6jcfzNFGVF8PAgARL@dpg-d8gusdr7uimc73calibg-a.frankfurt-postgres.render.com/nkulawua'

# Connect to PostgreSQL and truncate
pg = psycopg2.connect(PG_URL)
pg.autocommit = False
pg_cur = pg.cursor()

pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name LIKE 'accounting_app_%'")
tables = [r[0] for r in pg_cur.fetchall()]
for t in tables:
    pg_cur.execute(f'TRUNCATE TABLE "{t}" CASCADE')
pg_cur.execute('TRUNCATE TABLE "auth_user" CASCADE')
pg.commit()
print('Truncated all tables')

# Connect to SQLite
sqlite_path = r'D:\Mantchombe websites\nkula_wua-main\db.sqlite3'
sqlite = sqlite3.connect(sqlite_path)
sqlite.row_factory = sqlite3.Row
sqlite_cur = sqlite.cursor()

# Get all tables from SQLite
sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%' AND name NOT LIKE 'auth_%' ORDER BY name")
tables_to_transfer = [r[0] for r in sqlite_cur.fetchall()]

# Define table order (parent tables first to respect FK constraints)
# We'll use multiple passes
all_tables = [
    # Level 0: no dependencies
    'accounting_app_account',
    'accounting_app_village',
    'accounting_app_scheme',
    'accounting_app_galleryimage',
    'accounting_app_landingpagesettings',
    'accounting_app_service',
    'accounting_app_taxrate',
    'accounting_app_boardoftrustees',
    'accounting_app_generalassemblymember',
    # Level 1: depends on village/scheme/account
    'accounting_app_beneficiary',
    'accounting_app_vendor',
    'accounting_app_employee',
    'accounting_app_budget',
    # Level 2: depends on beneficiary/vendor
    'accounting_app_invoice',
    'accounting_app_expense',
    'accounting_app_openingbalance',
    'accounting_app_beneficiaryhistory',
    'accounting_app_beneficiarystatuslog',
    'accounting_app_loginsession',
    'accounting_app_userprofile',
    'accounting_app_balancehistory',
    'accounting_app_communicationlog',
    # Level 3: depends on invoice/expense
    'accounting_app_payment',
    'accounting_app_invoiceitem',
    'accounting_app_expenseitem',
    'accounting_app_budgetline',
    'accounting_app_employeesalary',
    'accounting_app_journalentry',
    'accounting_app_journalentryline',
    'accounting_app_report',
    'accounting_app_villagepopulation',
    'accounting_app_yearendrollover',
    # Level 4: misc
    'accounting_app_activitylog',
    'accounting_app_usermessage',
    'accounting_app_usercall',
    'accounting_app_deletedrecord',
    'accounting_app_datamigrationlog',
    'accounting_app_systemupdatelog',
    'accounting_app_systemversion',
]

# Filter to only existing tables
existing_tables = []
sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_sqlite_tables = set(r[0] for r in sqlite_cur.fetchall())

# Get PG columns for our tables
pg_cur.execute("SELECT table_name, column_name, ordinal_position, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position")
pg_columns = {}
for t, c, pos, dtype, charlen, nullable in pg_cur.fetchall():
    if t.startswith('accounting_app_'):
        if t not in pg_columns:
            pg_columns[t] = []
        pg_columns[t].append({
            'name': c,
            'type': dtype,
            'nullable': nullable == 'YES'
        })

print(f'PG tables with columns: {list(pg_columns.keys())}')

total_rows = 0

for table in all_tables:
    if table not in all_sqlite_tables:
        print(f'SKIP {table}: not in SQLite')
        continue
    if table not in pg_columns:
        print(f'SKIP {table}: not in PG')
        continue
    
    # Get columns for this table
    cols = pg_columns[table]
    col_names = [c['name'] for c in cols]
    
    # PK column is usually 'id'
    col_names_str = ', '.join(f'"{c}"' for c in col_names)
    placeholders = ', '.join(['%s'] * len(col_names))
    
    # Read data from SQLite
    sqlite_cur.execute(f'SELECT * FROM "{table}"')
    rows_data = sqlite_cur.fetchall()
    
    if not rows_data:
        print(f'  {table}: 0 rows (empty)')
        continue
    
    # Build rows matching PG column order
    rows = []
    for row in rows_data:
        row_dict = dict(row)
        pg_row = []
        for col in col_names:
            val = row_dict.get(col)
            pg_row.append(val)
        rows.append(pg_row)
    
    # Batch insert
    BATCH = 200
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        query = f'INSERT INTO "{table}" ({col_names_str}) VALUES %s ON CONFLICT DO NOTHING'
        try:
            execute_values(pg_cur, query, batch, template=None, page_size=BATCH)
            pg.commit()
            inserted += len(batch)
        except Exception as e:
            pg.rollback()
            print(f'  ERROR in {table} batch {i}: {e}')
            # Try row by row
            for row in batch:
                try:
                    execute_values(pg_cur, query, [row], template=None, page_size=1)
                    pg.commit()
                    inserted += 1
                except Exception as e2:
                    pg.rollback()
                    # Skip problematic row
    
    total_rows += inserted
    print(f'  {table}: {inserted}/{len(rows_data)} rows')

# Also transfer auth_user
print('\nTransferring auth tables...')
for table in ['auth_user']:
    if table not in all_sqlite_tables:
        print(f'SKIP {table}: not in SQLite')
        continue
    
    sqlite_cur.execute(f'SELECT * FROM "{table}"')
    rows_data = sqlite_cur.fetchall()
    if not rows_data:
        continue
    
    pg_cur.execute(f"SELECT column_name, ordinal_position FROM information_schema.columns WHERE table_schema='public' AND table_name='{table}' ORDER BY ordinal_position")
    col_names = [r[0] for r in pg_cur.fetchall()]
    col_names_str = ', '.join(f'"{c}"' for c in col_names)
    placeholders = ', '.join(['%s'] * len(col_names))
    
    rows = []
    for row in rows_data:
        row_dict = dict(row)
        pg_row = [row_dict.get(c) for c in col_names]
        rows.append(pg_row)
    
    BATCH = 100
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        query = f'INSERT INTO "{table}" ({col_names_str}) VALUES %s ON CONFLICT DO NOTHING'
        try:
            execute_values(pg_cur, query, batch, template=None, page_size=BATCH)
            pg.commit()
            inserted += len(batch)
        except Exception as e:
            pg.rollback()
            for row in batch:
                try:
                    execute_values(pg_cur, query, [row], template=None, page_size=1)
                    pg.commit()
                    inserted += 1
                except:
                    pg.rollback()
    
    total_rows += inserted
    print(f'  {table}: {inserted}/{len(rows_data)} rows')

sqlite.close()
pg_cur.close()
pg.close()
print(f'\nTotal: {total_rows} rows transferred')
