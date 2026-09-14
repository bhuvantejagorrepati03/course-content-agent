from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class COPOMapping(Base):
    __tablename__ = "co_po_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    co_number: Mapped[str] = mapped_column(String(10), nullable=False)   # e.g. "CO1"
    po_number: Mapped[str] = mapped_column(String(10), nullable=False)   # e.g. "PO1" or "PSO1"
    value: Mapped[int] = mapped_column(Integer, default=0)               # 0–3

    course: Mapped["Course"] = relationship("Course", back_populates="mappings")  # type: ignore[name-defined]
