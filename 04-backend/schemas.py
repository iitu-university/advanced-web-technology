from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
    )


class CourseOut(CamelModel):
    id: str
    title: str
    description: str
    credits: int
    is_elective: bool
    likes: int
    level: str


class StudentIn(CamelModel):
    name: str = Field(min_length=2)
    email: EmailStr


class StudentOut(StudentIn):
    id: int


class EnrollmentIn(CamelModel):
    course_id: str
    student_id: int


class EnrollmentOut(CamelModel):
    id: int
    course_id: str
    student_id: int
    enrolled_at: datetime


class EnrollmentDetail(EnrollmentOut):
    course_title: str
    student_name: str


class CourseStats(CamelModel):
    course_id: str
    enrolled: int
