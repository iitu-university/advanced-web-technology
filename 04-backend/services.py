"""Application rules shared by the REST and GraphQL transports."""

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Course, Enrollment, Student


CONSTRAINT_ERRORS = {
    "students_email_key": ("EMAIL_TAKEN", "Student with this email already exists"),
    "enrollments_course_id_student_id_key": (
        "ALREADY_ENROLLED", "Student is already enrolled in this course"
    ),
    "enrollments_course_id_fkey": ("COURSE_NOT_FOUND", "Course not found"),
    "enrollments_student_id_fkey": ("STUDENT_NOT_FOUND", "Student not found"),
}


class ServiceError(Exception):
    """An expected application error translated by the transport layer."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        known = CONSTRAINT_ERRORS.get(constraint)
        if known is None:
            raise
        raise ServiceError(*known) from exc


def create_student(db: Session, name: str, email: str) -> Student:
    if len(name.strip()) < 2:
        raise ServiceError("INVALID_NAME", "Name must have at least 2 characters")
    student = Student(name=name, email=email)
    db.add(student)
    commit(db)
    return student


def enroll(db: Session, course_id: str, student_id: int) -> Enrollment:
    enrollment = Enrollment(course_id=course_id, student_id=student_id)
    db.add(enrollment)
    commit(db)
    return enrollment


def like_course(db: Session, course_id: str) -> Course:
    stmt = (
        update(Course)
        .where(Course.id == course_id)
        .values(likes=Course.likes + 1)
        .returning(Course)
    )
    course = db.scalars(stmt).one_or_none()
    if course is None:
        raise ServiceError("COURSE_NOT_FOUND", "Course not found")
    commit(db)
    return course
