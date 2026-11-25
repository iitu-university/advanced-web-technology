"""Strawberry GraphQL schema sharing the REST services and database."""

from collections import defaultdict
from datetime import datetime
from typing import Annotated

import strawberry
from fastapi import Depends
from graphql import GraphQLError
from sqlalchemy import select
from sqlalchemy.orm import Session
from strawberry.dataloader import DataLoader
from strawberry.extensions import (
    DisableIntrospection,
    MaskErrors,
    MaxAliasesLimiter,
    QueryDepthLimiter,
)
from strawberry.fastapi import BaseContext, GraphQLRouter
from strawberry.permission import BasePermission
from strawberry.types import Info

import services
from auth import SessionDep, can_access_student, get_optional_user
from config import settings
from models import Course, Enrollment, Student, User


def check_limit(limit: int) -> int:
    if not 1 <= limit <= 100:
        raise GraphQLError("limit must be between 1 and 100")
    return limit


def parse_id(value: strawberry.ID) -> int:
    try:
        return int(value)
    except ValueError:
        raise GraphQLError(f"Invalid ID: {value!r}") from None


def should_mask(error: GraphQLError) -> bool:
    """Keep query validation and deliberate GraphQLErrors visible; hide crashes."""
    original = error.original_error
    return original is not None and not isinstance(original, GraphQLError)


def batch_loader(db: Session, column, many: bool = False) -> DataLoader:
    model = column.class_

    async def load(keys: list) -> list:
        rows = db.scalars(select(model).where(column.in_(keys))).all()
        groups = defaultdict(list)
        for row in rows:
            groups[getattr(row, column.key)].append(row)
        if many:
            return [groups[key] for key in keys]
        return [groups[key][0] if groups[key] else None for key in keys]

    return DataLoader(load_fn=load)


class Context(BaseContext):
    def __init__(self, db: Session, user: User | None):
        super().__init__()
        self.db = db
        self.user = user
        self.course_loader = batch_loader(db, Course.id)
        self.student_loader = batch_loader(db, Student.id)
        self.enrollments_of_course = batch_loader(db, Enrollment.course_id, many=True)
        self.enrollments_of_student = batch_loader(db, Enrollment.student_id, many=True)


def get_context(db: SessionDep, user: Annotated[User | None, Depends(get_optional_user)]) -> Context:
    return Context(db, user)


class IsAuthenticated(BasePermission):
    message = "Authentication required"

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        return info.context.user is not None


class IsAdmin(BasePermission):
    message = "Admin role required"

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        user = info.context.user
        return user is not None and user.role == "admin"


class IsSelfOrAdmin(BasePermission):
    message = "Not allowed to read this field"

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        user = info.context.user
        return user is not None and can_access_student(user, int(source.id))


@strawberry.type(name="User")
class UserType:
    id: strawberry.ID
    email: str
    role: str


@strawberry.type(name="Course")
class CourseType:
    id: strawberry.ID
    title: str
    description: str
    credits: int
    is_elective: bool
    likes: int
    level: str

    @strawberry.field
    async def enrollments(self, info: Info) -> list["EnrollmentType"]:
        return await info.context.enrollments_of_course.load(str(self.id))


@strawberry.type(name="Student")
class StudentType:
    id: strawberry.ID
    name: str
    email: str | None = strawberry.field(permission_classes=[IsSelfOrAdmin])

    @strawberry.field
    async def enrollments(self, info: Info) -> list["EnrollmentType"]:
        return await info.context.enrollments_of_student.load(int(self.id))


@strawberry.type(name="Enrollment")
class EnrollmentType:
    id: strawberry.ID
    enrolled_at: datetime
    course_id: strawberry.Private[str]
    student_id: strawberry.Private[int]

    @strawberry.field
    async def course(self, info: Info) -> CourseType:
        return await info.context.course_loader.load(self.course_id)

    @strawberry.field
    async def student(self, info: Info) -> StudentType:
        return await info.context.student_loader.load(self.student_id)


@strawberry.type
class UserError:
    code: str
    message: str


@strawberry.input
class EnrollInput:
    course_id: strawberry.ID
    student_id: strawberry.ID


@strawberry.type
class EnrollPayload:
    enrollment: EnrollmentType | None = None
    user_errors: list[UserError] = strawberry.field(default_factory=list)


@strawberry.type
class LikePayload:
    course: CourseType | None = None
    user_errors: list[UserError] = strawberry.field(default_factory=list)


@strawberry.input
class CreateStudentInput:
    name: str
    email: str


@strawberry.type
class CreateStudentPayload:
    student: StudentType | None = None
    user_errors: list[UserError] = strawberry.field(default_factory=list)


def as_user_errors(err: services.ServiceError) -> list[UserError]:
    return [UserError(code=err.code, message=err.message)]


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def me(self, info: Info) -> UserType:
        return info.context.user

    @strawberry.field
    def courses(
        self, info: Info, is_elective: bool | None = None, limit: int = 20
    ) -> list[CourseType]:
        stmt = select(Course).order_by(Course.likes.desc(), Course.id).limit(check_limit(limit))
        if is_elective is not None:
            stmt = stmt.where(Course.is_elective == is_elective)
        return info.context.db.scalars(stmt).all()

    @strawberry.field
    def course(self, info: Info, id: strawberry.ID) -> CourseType | None:
        return info.context.db.get(Course, str(id))

    @strawberry.field(permission_classes=[IsAdmin])
    def students(self, info: Info, limit: int = 20) -> list[StudentType]:
        stmt = select(Student).order_by(Student.id).limit(check_limit(limit))
        return info.context.db.scalars(stmt).all()

    @strawberry.field
    def student(self, info: Info, id: strawberry.ID) -> StudentType | None:
        return info.context.db.get(Student, parse_id(id))

    @strawberry.field
    def enrollments(self, info: Info, limit: int = 20) -> list[EnrollmentType]:
        stmt = select(Enrollment).order_by(Enrollment.id).limit(check_limit(limit))
        return info.context.db.scalars(stmt).all()


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_student(self, info: Info, input: CreateStudentInput) -> CreateStudentPayload:
        try:
            student = services.create_student(info.context.db, input.name, input.email)
        except services.ServiceError as err:
            return CreateStudentPayload(user_errors=as_user_errors(err))
        return CreateStudentPayload(student=student)

    @strawberry.mutation
    def enroll(self, info: Info, input: EnrollInput) -> EnrollPayload:
        try:
            enrollment = services.enroll(
                info.context.db, str(input.course_id), parse_id(input.student_id)
            )
        except services.ServiceError as err:
            return EnrollPayload(user_errors=as_user_errors(err))
        return EnrollPayload(enrollment=enrollment)

    @strawberry.mutation
    def like_course(self, info: Info, id: strawberry.ID) -> LikePayload:
        try:
            course = services.like_course(info.context.db, str(id))
        except services.ServiceError as err:
            return LikePayload(user_errors=as_user_errors(err))
        return LikePayload(course=course)


extensions = [
    QueryDepthLimiter(max_depth=5),
    MaxAliasesLimiter(max_alias_count=10),
    MaskErrors(should_mask_error=should_mask),
]
if not settings.graphql_introspection:
    extensions.append(DisableIntrospection())

schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=extensions)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
