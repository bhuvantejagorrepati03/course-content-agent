"""Quick import check — exits 0 if all imports succeed."""
import sys
sys.path.insert(0, ".")

errors = []

def try_import(module, label):
    try:
        __import__(module)
        print(f"  OK  {label}")
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        errors.append(label)

try_import("app.models.course", "models.course (new fields)")
try_import("app.models.unit", "models.unit")
try_import("app.models.document", "models.document")
try_import("app.schemas.course", "schemas.course (new fields)")
try_import("app.services.curriculum_parser", "services.curriculum_parser")
try_import("app.services.syllabus_processor", "services.syllabus_processor")
try_import("app.api.courses", "api.courses (regulations_router)")
try_import("app.main", "app.main (full app)")

if errors:
    print(f"\nFAILED imports: {errors}")
    sys.exit(1)
else:
    print("\nAll imports OK")
