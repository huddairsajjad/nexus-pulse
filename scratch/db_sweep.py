import sqlite3
db_path = r'C:\Users\STONE\Desktop\rabbi\database\nexus_vault.db'
conn = sqlite3.connect(db_path)
tables = ['vault_leads','outreach_queue','inbox_replies','blacklist_rules','suppressed_entities','dnc_blacklist','dedup_registry','followup_sequences']
for t in tables:
    try:
        cnt_before = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        conn.execute(f'DELETE FROM {t}')
        print(f'Cleared {t}: {cnt_before} rows removed')
    except Exception as e:
        print(f'Skip {t}: {e}')
conn.execute("DELETE FROM operator_sessions WHERE action != 'INITIAL_SETUP'")
conn.commit()
conn.close()
print('DB sweep complete')
