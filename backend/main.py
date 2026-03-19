import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

# --- Migrations ---
_inspector = inspect(engine)
_tables = _inspector.get_table_names()

# Migration: add layout columns to blocks table
if "blocks" in _tables:
    _existing = [col["name"] for col in _inspector.get_columns("blocks")]
    with engine.begin() as _conn:
        for _col, _default in [("x", 0), ("y", 0), ("w", 280), ("h", 0)]:
            if _col not in _existing:
                _conn.execute(text(f"ALTER TABLE blocks ADD COLUMN {_col} INTEGER NOT NULL DEFAULT {_default}"))
        # Migration: add page_id to blocks
        if "page_id" not in _existing:
            _conn.execute(text("ALTER TABLE blocks ADD COLUMN page_id INTEGER"))
        # Migration: add template_type to blocks
        if "template_type" not in _existing:
            _conn.execute(text("ALTER TABLE blocks ADD COLUMN template_type TEXT"))

# Migration: create default pages for projects with blocks and assign blocks
if "pages" in _tables and "blocks" in _tables:
    with engine.begin() as _conn:
        _orphan_projects = _conn.execute(text(
            "SELECT DISTINCT b.project_id FROM blocks b "
            "WHERE b.page_id IS NULL"
        )).fetchall()
        for (_pid,) in _orphan_projects:
            # Find or create a default page for this project
            _page = _conn.execute(text(
                "SELECT id FROM pages WHERE project_id = :pid ORDER BY position LIMIT 1"
            ), {"pid": _pid}).fetchone()
            if _page:
                _page_id = _page[0]
            else:
                _conn.execute(text(
                    "INSERT INTO pages (project_id, name, position, created_at, updated_at) "
                    "VALUES (:pid, '預設', 0, datetime('now'), datetime('now'))"
                ), {"pid": _pid})
                _page_id = _conn.execute(text("SELECT last_insert_rowid()")).scalar()
            _conn.execute(text(
                "UPDATE blocks SET page_id = :page_id WHERE project_id = :pid AND page_id IS NULL"
            ), {"page_id": _page_id, "pid": _pid})

# Migration: convert all non-markdown blocks to markdown format
if "blocks" in _tables:
    with engine.begin() as _conn:
        _rows = _conn.execute(text(
            "SELECT id, block_type, content FROM blocks WHERE block_type != 'markdown'"
        )).fetchall()
        for _id, _btype, _raw in _rows:
            _c = json.loads(_raw)
            if _btype == "text":
                _md = _c.get("text", "")
            elif _btype == "link":
                _title = _c.get("title") or _c.get("url", "")
                _url = _c.get("url", "")
                _desc = _c.get("description", "")
                _md = f"[{_title}]({_url})"
                if _desc:
                    _md += f"\n\n{_desc}"
            elif _btype == "list":
                _md = "\n".join(f"- {item}" for item in _c.get("items", []))
            elif _btype == "checklist":
                lines = []
                for item in _c.get("items", []):
                    mark = "x" if item.get("checked") else " "
                    lines.append(f"- [{mark}] {item.get('text', '')}")
                _md = "\n".join(lines)
            elif _btype == "image":
                _caption = _c.get("caption", "")
                _url = _c.get("url", "")
                _md = f"![{_caption}]({_url})"
            else:
                _md = str(_c)
            _conn.execute(text(
                "UPDATE blocks SET block_type = 'markdown', content = :content WHERE id = :id"
            ), {"content": json.dumps({"text": _md}), "id": _id})

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_origin_regex=r"https://.*\.ts\.net",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# --- helpers ---

def get_or_create_tag(db: Session, name: str) -> models.Tag:
    tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if not tag:
        tag = models.Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


def project_to_out(project: models.Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "tags": project.tags,
        "block_count": len(project.blocks),
    }


def block_to_out(block: models.Block) -> dict:
    return {
        "id": block.id,
        "project_id": block.project_id,
        "page_id": block.page_id,
        "block_type": block.block_type,
        "content": json.loads(block.content),
        "position": block.position,
        "x": block.x,
        "y": block.y,
        "w": block.w,
        "h": block.h,
        "template_type": block.template_type,
        "created_at": block.created_at,
        "updated_at": block.updated_at,
    }


# --- Project endpoints ---

@app.get("/api/projects", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).order_by(models.Project.updated_at.desc()).all()
    return [project_to_out(p) for p in projects]


@app.post("/api/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(body: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project = models.Project(
        name=body.name,
        description=body.description,
    )
    project.tags = [get_or_create_tag(db, t) for t in body.tags]
    db.add(project)
    db.flush()
    # Create a default page
    page = models.Page(project_id=project.id, name="預設", position=0)
    db.add(page)
    db.commit()
    db.refresh(project)
    return project_to_out(project)


@app.put("/api/projects/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, body: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = body.name
    project.description = body.description
    project.tags = [get_or_create_tag(db, t) for t in body.tags]

    db.commit()
    db.refresh(project)
    return project_to_out(project)


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


# --- Page endpoints ---

@app.get("/api/projects/{project_id}/pages", response_model=list[schemas.PageOut])
def list_pages(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.pages


@app.post("/api/projects/{project_id}/pages", response_model=schemas.PageOut, status_code=201)
def create_page(project_id: int, body: schemas.PageCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    position = len(project.pages)
    page = models.Page(project_id=project_id, name=body.name, position=position)
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@app.put("/api/pages/{page_id}", response_model=schemas.PageOut)
def update_page(page_id: int, body: schemas.PageUpdate, db: Session = Depends(get_db)):
    page = db.query(models.Page).filter(models.Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    page.name = body.name
    db.commit()
    db.refresh(page)
    return page


@app.delete("/api/pages/{page_id}", status_code=204)
def delete_page(page_id: int, db: Session = Depends(get_db)):
    page = db.query(models.Page).filter(models.Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    # Don't allow deleting the last page
    count = db.query(models.Page).filter(models.Page.project_id == page.project_id).count()
    if count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last page")
    db.delete(page)
    db.commit()


# --- Block endpoints ---

@app.get("/api/pages/{page_id}/blocks", response_model=list[schemas.BlockOut])
def list_page_blocks(page_id: int, db: Session = Depends(get_db)):
    page = db.query(models.Page).filter(models.Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return [block_to_out(b) for b in page.blocks]


@app.post("/api/pages/{page_id}/blocks", response_model=schemas.BlockOut, status_code=201)
def create_page_block(page_id: int, body: schemas.BlockCreate, db: Session = Depends(get_db)):
    page = db.query(models.Page).filter(models.Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    block = models.Block(
        project_id=page.project_id,
        page_id=page_id,
        block_type=body.block_type,
        content=json.dumps(body.content),
        position=body.position,
        x=body.x,
        y=body.y,
        w=body.w,
        h=body.h,
        template_type=body.template_type,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block_to_out(block)


# Keep legacy project-level block listing for backward compat
@app.get("/api/projects/{project_id}/blocks", response_model=list[schemas.BlockOut])
def list_blocks(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return [block_to_out(b) for b in project.blocks]


@app.put("/api/blocks/{block_id}", response_model=schemas.BlockOut)
def update_block(block_id: int, body: schemas.BlockUpdate, db: Session = Depends(get_db)):
    block = db.query(models.Block).filter(models.Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    if body.block_type is not None:
        block.block_type = body.block_type
    if body.content is not None:
        block.content = json.dumps(body.content)
    if body.x is not None:
        block.x = body.x
    if body.y is not None:
        block.y = body.y
    if body.w is not None:
        block.w = body.w
    if body.h is not None:
        block.h = body.h
    if body.template_type is not None:
        block.template_type = body.template_type

    db.commit()
    db.refresh(block)
    return block_to_out(block)


@app.delete("/api/blocks/{block_id}", status_code=204)
def delete_block(block_id: int, db: Session = Depends(get_db)):
    block = db.query(models.Block).filter(models.Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    db.delete(block)
    db.commit()


@app.put("/api/blocks/{block_id}/layout", response_model=schemas.BlockOut)
def update_block_layout(block_id: int, body: schemas.BlockLayout, db: Session = Depends(get_db)):
    block = db.query(models.Block).filter(models.Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    block.x = body.x
    block.y = body.y
    block.w = body.w
    block.h = body.h
    db.commit()
    db.refresh(block)
    return block_to_out(block)


@app.put("/api/projects/{project_id}/blocks/reorder")
def reorder_blocks(project_id: int, body: schemas.ReorderRequest, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    block_map = {b.id: b for b in project.blocks}
    for item in body.items:
        if item.id in block_map:
            block_map[item.id].position = item.position

    db.commit()
    return {"ok": True}


# --- Upload endpoint ---

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        ext = Path(file.filename).suffix.lower()
        allowed = {
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
            ".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv", ".md",
        }
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"不支援的檔案格式：{ext}")

        content = await file.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="檔案大小超過 20MB 限制")

        filename = f"{uuid.uuid4().hex}{ext}"
        dest = UPLOAD_DIR / filename
        dest.write_bytes(content)

        return {"url": f"/uploads/{filename}", "original_name": file.filename}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="上傳過程發生錯誤，請稍後再試")


# --- Tags ---

@app.get("/api/tags", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).order_by(models.Tag.name).all()


# --- Serve frontend SPA (production) ---

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Try to serve the exact file first
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Fall back to index.html for SPA routing
        return FileResponse(FRONTEND_DIST / "index.html")
