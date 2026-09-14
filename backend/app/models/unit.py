from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    unit_number: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hours: Mapped[int] = mapped_column(Integer, default=8)
    co_mapping: Mapped[str | None] = mapped_column(String(200), nullable=True)  # comma-separated CO codes
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    course: Mapped["Course"] = relationship("Course", back_populates="units")  # type: ignore[name-defined]
    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="unit", cascade="all, delete-orphan", order_by="Topic.topic_order")  # type: ignore[name-defined]
