from app.db.database import engine
from sqlalchemy import text

conn = engine.connect()
result = conn.execute(text("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND (name LIKE 'ix_%' OR name LIKE 'uq_%') ORDER BY tbl_name"))
for r in result.fetchall():
    print(f"  {r[1]:25s} -> {r[0]}")
conn.close()
print("Done")
