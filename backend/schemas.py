from datetime import datetime
from pydantic import BaseModel


# --- Tag ---

class TagOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


# --- Page ---

class PageCreate(BaseModel):
    name: str = "新分頁"

class PageUpdate(BaseModel):
    name: str

class PageOut(BaseModel):
    id: int
    project_id: int
    name: str
    position: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# --- Block ---

class BlockCreate(BaseModel):
    block_type: str = "markdown"
    content: dict = {}
    position: int = 0
    x: int = 0
    y: int = 0
    w: int = 280
    h: int = 0
    template_type: str | None = None


class BlockUpdate(BaseModel):
    block_type: str | None = None
    content: dict | None = None
    x: int | None = None
    y: int | None = None
    w: int | None = None
    h: int | None = None
    template_type: str | None = None


class BlockLayout(BaseModel):
    x: int
    y: int
    w: int
    h: int = 0


class BlockOut(BaseModel):
    id: int
    project_id: int
    page_id: int | None
    block_type: str
    content: dict
    position: int
    x: int
    y: int
    w: int
    h: int
    template_type: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ReorderItem(BaseModel):
    id: int
    position: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]


# --- Project ---

class ProjectBase(BaseModel):
    name: str
    description: str = ""


class ProjectCreate(ProjectBase):
    tags: list[str] = []


class ProjectUpdate(ProjectBase):
    tags: list[str] = []


class ProjectOut(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut] = []
    block_count: int = 0
    model_config = {"from_attributes": True}
