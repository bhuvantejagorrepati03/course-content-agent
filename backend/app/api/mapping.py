"""CO-PO-PSO mapping endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.mapping import COPOMapping
from app.schemas.common import ApiResponse
from app.schemas.course import MappingMatrixOut, MappingRow

router = APIRouter(prefix="/api/mapping", tags=["mapping"])


@router.get("/{course_id}", response_model=ApiResponse)
def get_mapping(course_id: int, db: Session = Depends(get_db)):
    rows = db.query(COPOMapping).filter(COPOMapping.course_id == course_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No mapping data found for this course")

    co_map: dict[str, dict[str, int]] = {}
    col_set: set[str] = set()
    for r in rows:
        co_map.setdefault(r.co_number, {})[r.po_number] = r.value
        col_set.add(r.po_number)

    def _key(c: str):
        prefix = "A" if c.startswith("PO") else "B"
        num = int(c[2:]) if c[2:].isdigit() else 0
        return (prefix, num)

    columns = sorted(col_set, key=_key)
    matrix = [
        MappingRow(co=co, values={col: vals.get(col, 0) for col in columns})
        for co, vals in sorted(co_map.items())
    ]
    return ApiResponse.ok(MappingMatrixOut(course_id=course_id, matrix=matrix, columns=columns))
