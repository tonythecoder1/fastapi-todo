from pydantic import BaseModel, Field


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=300)
    priority: int = Field(gt=0, lt=10)
    complete: bool 