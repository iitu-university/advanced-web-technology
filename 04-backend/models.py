from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("credits > 0", name="credits"),
        CheckConstraint("likes >= 0", name="likes"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    credits: Mapped[int]
    is_elective: Mapped[bool] = mapped_column(server_default=text("false"))
    likes: Mapped[int] = mapped_column(server_default=text("0"))

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", passive_deletes=True
    )


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (CheckConstraint("char_length(name) >= 2", name="name"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", passive_deletes=True
    )


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("course_id", "student_id"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT")
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(server_default=func.now())

    course: Mapped[Course] = relationship(back_populates="enrollments")
    student: Mapped[Student] = relationship(back_populates="enrollments")
