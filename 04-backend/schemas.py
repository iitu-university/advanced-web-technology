from pydantic import BaseModel, ConfigDict
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
