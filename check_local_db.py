import sqlite3, os, json

db_path = os.path.join(os.getcwd(), 'db.sqlite3')
if not os.path.exists(db_path):
    print('No db.sqlite3 found')
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cur.fetchall()
    for t in tables:
        name = t[0]
        if name.startswith('accounting_app') or name in ('auth_user',):
            cur.execute(f'SELECT COUNT(*) FROM "{name}"')
            count = cur.fetchone()[0]
            print(f'{name}: {count}')
    conn.close()

print()
print('--- seed_data.json ---')
with open('seed_data.json') as f:
    data = json.load(f)
from collections import Counter
c = Counter(r['model'] for r in data)
for k, v in sorted(c.items()):
    print(f'{k}: {v}')
