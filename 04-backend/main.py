from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query

from data import find_course, get_all_courses
from models import Course


app = FastAPI(title="Course Catalog API")


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
