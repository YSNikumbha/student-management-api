from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int


def build_paginated_response(
    items: list[T],
    page: int,
    page_size: int,
    total_items: int,
) -> dict[str, list[T] | int]:
    total_pages = ceil(total_items / page_size) if total_items else 0
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
    }


def get_offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size
