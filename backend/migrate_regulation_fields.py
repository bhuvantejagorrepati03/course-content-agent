"""
Safe one-time migration.

Adds:
  courses.source_type  VARCHAR(20) DEFAULT 'seed'   — "seed" | "imported"
  courses.branch       VARCHAR(100) DEFAULT ''       — detected branch/dept short form

Safe to run multiple times (idempotent — skips if column already present).
"""
import sqlite3
import pathlib

DB_PATH = pathlib.Path("data/app.db")

if not DB_PATH.exists():
    print(f"Database not found at {DB_PATH} — nothing to migrate.")
    raise SystemExit(0)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA table_info(courses)")
existing = {row[1] for row in cur.fetchall()}
print(f"Existing courses columns: {sorted(existing)}")

added = []
if "source_type" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN source_type VARCHAR(20) DEFAULT 'seed'")
    added.append("source_type")

if "branch" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN branch VARCHAR(100) DEFAULT ''")
    added.append("branch")

if "l_hours" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN l_hours INTEGER DEFAULT 0")
    added.append("l_hours")

if "t_hours" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN t_hours INTEGER DEFAULT 0")
    added.append("t_hours")

if "p_hours" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN p_hours INTEGER DEFAULT 0")
    added.append("p_hours")

if "course_objectives" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN course_objectives TEXT DEFAULT NULL")
    added.append("course_objectives")

# Mark existing seeded courses explicitly
cur.execute("UPDATE courses SET source_type = 'seed' WHERE source_type IS NULL OR source_type = 'seed'")

conn.commit()
conn.close()

if added:
    print(f"Added columns: {added}")
else:
    print("All columns already present — no changes made.")

print("Migration complete.")
