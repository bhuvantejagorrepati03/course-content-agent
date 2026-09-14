"""Fix DB state: remove bad UNKNOWN courses, reset doc 2 for reprocessing."""
import sqlite3

conn = sqlite3.connect("data/app.db")
cur = conn.cursor()

cur.execute("DELETE FROM courses WHERE course_code = 'UNKNOWN'")
print(f"Deleted {cur.rowcount} UNKNOWN courses")

cur.execute("UPDATE syllabus_documents SET status='uploaded', error_message=NULL WHERE id=2")
print(f"Reset document 2 status to uploaded")

conn.commit()

cur.execute("SELECT id, original_filename, status, file_size FROM syllabus_documents")
print("Documents:", cur.fetchall())
cur.execute("SELECT id, course_code, regulation, source_type FROM courses")
print("Courses:", cur.fetchall())
conn.close()
print("Done.")
