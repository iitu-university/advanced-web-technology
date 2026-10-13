import os
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data import find_course, get_all_courses
from models import Course, Enrollment, EnrollmentIn


app = FastAPI(title="Course Catalog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

ENROLLMENTS: list[Enrollment] = []


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Course Catalog API is running"}


def pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, int]:
    return {"offset": (page - 1) * page_size, "limit": page_size}


@app.get("/courses", response_model=list[Course])
def list_courses(
    is_elective: bool | None = None,
    sort: Literal["popular", "title"] = "popular",
    q: str | None = None,
    p: dict[str, int] = Depends(pagination),
) -> list[Course]:
    courses = get_all_courses()

    if is_elective is not None:
        courses = [course for course in courses if course.is_elective == is_elective]

    if q is not None:
        query = q.casefold()
        courses = [course for course in courses if query in course.title.casefold()]

    if sort == "title":
        courses = sorted(courses, key=lambda course: course.title)
    else:
        courses = sorted(courses, key=lambda course: course.likes, reverse=True)

    return courses[p["offset"] : p["offset"] + p["limit"]]


@app.get("/courses/{course_id}", response_model=Course)
def get_course(course_id: str) -> Course:
    course = find_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@app.post("/courses/{course_id}/like", response_model=Course)
def like_course(course_id: str) -> Course:
    course = find_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    course.likes += 1
    return course


@app.post("/enrollments", response_model=Enrollment, status_code=201)
def create_enrollment(data: EnrollmentIn) -> Enrollment:
    if find_course(data.course_id) is None:
        raise HTTPException(status_code=404, detail="Course not found")
    enrollment = Enrollment(
        id=len(ENROLLMENTS) + 1,
        course_id=data.course_id,
        student_name=data.student_name,
    )
    ENROLLMENTS.append(enrollment)
    return enrollment


@app.get("/enrollments", response_model=list[Enrollment])
def list_enrollments() -> list[Enrollment]:
    return ENROLLMENTS
