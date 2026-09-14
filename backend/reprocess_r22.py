"""
Reprocess document ID 2 (the R22 curriculum PDF) with the new curriculum parser.
"""
import asyncio
import sys
sys.path.insert(0, ".")

from app.database import SessionLocal, create_tables
from app.services.syllabus_processor import process_document
from app.models.document import SyllabusDocument

def main():
    create_tables()
    db = SessionLocal()
    try:
        doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == 2).first()
        if not doc:
            print("Document 2 not found")
            return
        print(f"Reprocessing: {doc.original_filename} ({doc.file_size:,} bytes)")
        print(f"File path: {doc.file_path}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_document(2, db))
        loop.close()

        # Refresh and report
        db.expire(doc)
        doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == 2).first()
        print(f"\nStatus: {doc.status}")
        print(f"Error: {doc.error_message}")
        print(f"Extracted: units={doc.extracted_units} topics={doc.extracted_topics} "
              f"outcomes={doc.extracted_outcomes} textbooks={doc.extracted_textbooks}")

        from app.models.course import Course
        imported = db.query(Course).filter(Course.source_type == "imported").all()
        print(f"\nImported courses ({len(imported)}):")
        for c in imported[:20]:
            print(f"  {c.course_code}  {c.course_name[:50]}  [{c.regulation}]")
        if len(imported) > 20:
            print(f"  ... and {len(imported) - 20} more")

        from app.services.vector_store import collection_count
        print(f"\nChromaDB chunk count: {collection_count()}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
