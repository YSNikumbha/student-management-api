from pydantic import BaseModel


class SearchResult(BaseModel):
    id: int
    title: str
    subtitle: str | None = None
    type: str
    url: str


class SearchResponse(BaseModel):
    students: list[SearchResult]
    courses: list[SearchResult]
    subjects: list[SearchResult]
    batches: list[SearchResult]
    users: list[SearchResult] = []
