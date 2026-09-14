from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Textbook(Base):
    __tablename__ = "textbooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str] = mapped_column(String(300), nullable=False)
    edition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    year: Mapped[str | None] = mapped_column(String(10), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(30), nullable=True)
    book_type: Mapped[str] = mapped_column(String(20), default="textbook")  # "textbook" | "reference"

    course: Mapped["Course"] = relationship("Course", back_populates="textbooks")  # type: ignore[name-defined]
