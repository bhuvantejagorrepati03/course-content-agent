from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    course_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    program: Mapped[str] = mapped_column(String(100), nullable=False)
    branch: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    department: Mapped[str] = mapped_column(String(150), nullable=False)
    year: Mapped[str] = mapped_column(String(50), nullable=False)
    semester: Mapped[str] = mapped_column(String(50), nullable=False)
    regulation: Mapped[str] = mapped_column(String(20), nullable=False)
    credits: Mapped[float] = mapped_column(Float, default=4.0)
    l_hours: Mapped[int] = mapped_column(Integer, default=0)   # Lecture hours / week
    t_hours: Mapped[int] = mapped_column(Integer, default=0)   # Tutorial hours / week
    p_hours: Mapped[int] = mapped_column(Integer, default=0)   # Practical hours / week
    total_hours: Mapped[int] = mapped_column(Integer, default=45)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    course_objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    # "seed" = demo/seeded data  |  "imported" = extracted from a real uploaded PDF
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="seed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    units: Mapped[list["Unit"]] = relationship("Unit", back_populates="course", cascade="all, delete-orphan", order_by="Unit.unit_number")  # type: ignore[name-defined]
    outcomes: Mapped[list["CourseOutcome"]] = relationship("CourseOutcome", back_populates="course", cascade="all, delete-orphan")  # type: ignore[name-defined]
    textbooks: Mapped[list["Textbook"]] = relationship("Textbook", back_populates="course", cascade="all, delete-orphan")  # type: ignore[name-defined]
    mappings: Mapped[list["COPOMapping"]] = relationship("COPOMapping", back_populates="course", cascade="all, delete-orphan")  # type: ignore[name-defined]
    documents: Mapped[list["SyllabusDocument"]] = relationship("SyllabusDocument", back_populates="course", cascade="all, delete-orphan")  # type: ignore[name-defined]
