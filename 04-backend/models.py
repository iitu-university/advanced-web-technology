from pydantic import BaseModel


class Course(BaseModel):
    id: str
    title: str
    description: str
    credits: int
    is_elective: bool = False
    likes: int = 0
