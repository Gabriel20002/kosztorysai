"""Statystyki bazy KNR"""
import sqlite3

conn = sqlite3.connect(r'C:\Users\Gabriel\clawd\kosztorysAI\knr_database\knr.db')
cur = conn.cursor()

print('=== KATALOGI (wg liczby tablic) ===')
cur.execute('''
    SELECT c.id, c.name, c.pages_count, 
           (SELECT COUNT(*) FROM positions WHERE catalog_id = c.id) as pos_count 
    FROM catalogs c 
    ORDER BY pos_count DESC
''')
for row in cur.fetchall():
    safe_name = row[1].encode('ascii', 'replace').decode('ascii')[:35]
    print(f'{row[0]:35} | {row[3]:4} tablic | {safe_name}')

print(f'\n=== STATYSTYKI ===')
cur.execute('SELECT COUNT(*) FROM catalogs')
print(f'Katalogi: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM positions')
print(f'Pozycje (tablice): {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM positions WHERE unit != '' AND unit != 'jm'")
print(f'Z jednostka: {cur.fetchone()[0]}')

print('\n=== SAMPLE POZYCJI ===')
cur.execute('SELECT full_code, description, unit FROM positions WHERE description != "" LIMIT 10')
for row in cur.fetchall():
    safe_desc = row[1].encode('ascii', 'replace').decode('ascii')[:50]
    print(f'{row[0]:25} | {safe_desc}... [{row[2]}]')

conn.close()
