"""
Project Board MCP Server
========================
Wraps the project-board REST API as MCP tools so that Claude Code
can natively list / create / update / delete blocks on the board.

Transport: stdio  (launched automatically by Claude Code)
"""

import json
import sys
import logging
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
log = logging.getLogger("project-board-mcp")

mcp = FastMCP("project-board")

API_BASE = "http://100.110.86.62:8001"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def api(method: str, path: str, **kwargs) -> dict | list | None:
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.request(method, url, **kwargs)
            r.raise_for_status()
            if r.status_code == 204:
                return {}
            return r.json()
        except httpx.HTTPStatusError as e:
            log.error("HTTP %s %s → %s", method, path, e.response.status_code, file=sys.stderr)
            return None
        except Exception as e:
            log.error("Request failed: %s", e, file=sys.stderr)
            return None


def fmt_project(p: dict) -> str:
    tags = ", ".join(t["name"] for t in p.get("tags", []))
    return (
        f"- **{p['name']}** (id:{p['id']})"
        f"  blocks:{p.get('block_count', 0)}"
        f"  tags:[{tags}]"
        f"  desc: {p.get('description', '')}"
    )


def fmt_block(b: dict) -> str:
    text = b.get("content", {}).get("text", "")
    preview = text[:120].replace("\n", " ")
    if len(text) > 120:
        preview += "…"
    tpl = f"  template:{b['template_type']}" if b.get("template_type") else ""
    return (
        f"- block:{b['id']}  type:{b['block_type']}{tpl}"
        f"  pos:({b['x']},{b['y']}) {b['w']}x{b['h']}\n"
        f"  content: {preview}"
    )


# ---------------------------------------------------------------------------
# Project tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_projects() -> str:
    """列出所有專案，包含 ID、名稱、標籤、block 數量。"""
    data = await api("GET", "/api/projects")
    if data is None:
        return "ERROR: 無法取得專案列表"
    if not data:
        return "目前沒有任何專案。"
    lines = ["# 專案列表", ""]
    for p in data:
        lines.append(fmt_project(p))
    return "\n".join(lines)


@mcp.tool()
async def create_project(
    name: str,
    description: str = "",
    tags: Optional[list[str]] = None,
) -> str:
    """建立新專案。建立後會自動產生一個「預設」分頁。

    Args:
        name: 專案名稱
        description: 專案描述
        tags: 標籤列表，例如 ["Unity", "AI"]
    """
    payload = {"name": name, "description": description, "tags": tags or []}
    data = await api("POST", "/api/projects", json=payload)
    if data is None:
        return "ERROR: 無法建立專案"
    return (
        f"專案建立成功！\n"
        f"- id: {data['id']}\n"
        f"- name: {data['name']}\n"
        f"- description: {data.get('description', '')}\n"
        f"接下來可用 list_pages(project_id={data['id']}) 取得預設分頁 ID，再建立 block。"
    )


@mcp.tool()
async def update_project(
    project_id: int,
    name: str,
    description: str = "",
    tags: Optional[list[str]] = None,
) -> str:
    """更新專案名稱、描述或標籤。

    Args:
        project_id: 專案 ID
        name: 新的專案名稱
        description: 新的專案描述
        tags: 新的標籤列表
    """
    payload = {"name": name, "description": description, "tags": tags or []}
    data = await api("PUT", f"/api/projects/{project_id}", json=payload)
    if data is None:
        return f"ERROR: 無法更新專案 {project_id}"
    return f"專案 {project_id} 更新成功。"


@mcp.tool()
async def delete_project(project_id: int) -> str:
    """刪除專案及其所有分頁和 blocks。此操作無法復原。

    Args:
        project_id: 要刪除的專案 ID
    """
    data = await api("DELETE", f"/api/projects/{project_id}")
    if data is None:
        return f"ERROR: 無法刪除專案 {project_id}"
    return f"專案 {project_id} 已刪除。"


# ---------------------------------------------------------------------------
# Page tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_pages(project_id: int) -> str:
    """列出指定專案的所有分頁。

    Args:
        project_id: 專案 ID
    """
    data = await api("GET", f"/api/projects/{project_id}/pages")
    if data is None:
        return f"ERROR: 無法取得專案 {project_id} 的分頁"
    if not data:
        return f"專案 {project_id} 沒有分頁。"
    lines = [f"# 專案 {project_id} 的分頁", ""]
    for pg in data:
        lines.append(f"- **{pg['name']}** (page_id:{pg['id']}, position:{pg['position']})")
    return "\n".join(lines)


@mcp.tool()
async def create_page(project_id: int, name: str = "新分頁") -> str:
    """在指定專案中建立新分頁。

    Args:
        project_id: 專案 ID
        name: 分頁名稱，預設「新分頁」
    """
    data = await api("POST", f"/api/projects/{project_id}/pages", json={"name": name})
    if data is None:
        return f"ERROR: 無法在專案 {project_id} 建立分頁"
    return (
        f"分頁建立成功！\n"
        f"- page_id: {data['id']}\n"
        f"- name: {data['name']}"
    )


@mcp.tool()
async def update_page(page_id: int, name: str) -> str:
    """重新命名分頁。

    Args:
        page_id: 分頁 ID
        name: 新的分頁名稱
    """
    data = await api("PUT", f"/api/pages/{page_id}", json={"name": name})
    if data is None:
        return f"ERROR: 無法更新分頁 {page_id}"
    return f"分頁 {page_id} 已重新命名為「{name}」。"


@mcp.tool()
async def delete_page(page_id: int) -> str:
    """刪除分頁及其上的所有 blocks。無法刪除專案的最後一個分頁。

    Args:
        page_id: 要刪除的分頁 ID
    """
    data = await api("DELETE", f"/api/pages/{page_id}")
    if data is None:
        return f"ERROR: 無法刪除分頁 {page_id}（可能是最後一個分頁）"
    return f"分頁 {page_id} 已刪除。"


# ---------------------------------------------------------------------------
# Block tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_blocks(page_id: int) -> str:
    """取得指定分頁上的所有 blocks。

    Args:
        page_id: 分頁 ID
    """
    data = await api("GET", f"/api/pages/{page_id}/blocks")
    if data is None:
        return f"ERROR: 無法取得 page {page_id} 的 blocks"
    if not data:
        return f"Page {page_id} 上沒有任何 block。"
    lines = [f"# Page {page_id} 的 Blocks ({len(data)} 個)", ""]
    for b in data:
        lines.append(fmt_block(b))
    return "\n".join(lines)


@mcp.tool()
async def get_block_detail(block_id: int) -> str:
    """取得單一 block 的完整內容（不截斷）。適合需要閱讀完整內容時使用。

    Args:
        block_id: Block ID
    """
    # Fetch all blocks from the project to find this one
    # Since there's no single-block endpoint, we search across projects
    projects = await api("GET", "/api/projects")
    if not projects:
        return "ERROR: 無法取得專案列表"
    for p in projects:
        blocks = await api("GET", f"/api/projects/{p['id']}/blocks")
        if blocks:
            for b in blocks:
                if b["id"] == block_id:
                    text = b.get("content", {}).get("text", "")
                    tpl = b.get("template_type") or "none"
                    return (
                        f"# Block {block_id}\n\n"
                        f"- project: {p['name']} (id:{p['id']})\n"
                        f"- page_id: {b.get('page_id')}\n"
                        f"- type: {b['block_type']}\n"
                        f"- template: {tpl}\n"
                        f"- position: ({b['x']}, {b['y']}) {b['w']}x{b['h']}\n\n"
                        f"## Content\n\n{text}"
                    )
    return f"ERROR: 找不到 block {block_id}"


@mcp.tool()
async def create_block(
    page_id: int,
    text: str,
    template_type: Optional[str] = None,
    x: int = 0,
    y: int = 0,
    w: int = 280,
) -> str:
    """在指定分頁建立新的 markdown block。

    Args:
        page_id: 要建立 block 的分頁 ID
        text: Block 的 markdown 內容
        template_type: 模板類型（link / image / list / todo / file），一般文字留空即可
        x: 水平位置（px）
        y: 垂直位置（px）
        w: 寬度（px），預設 280
    """
    payload = {
        "block_type": "markdown",
        "content": {"text": text},
        "x": x,
        "y": y,
        "w": w,
        "h": 0,
    }
    if template_type:
        payload["template_type"] = template_type

    data = await api("POST", f"/api/pages/{page_id}/blocks", json=payload)
    if data is None:
        return f"ERROR: 無法在 page {page_id} 建立 block"
    return (
        f"Block 建立成功！\n"
        f"- id: {data['id']}\n"
        f"- page_id: {data['page_id']}\n"
        f"- position: ({data['x']}, {data['y']}) {data['w']}x{data['h']}"
    )


@mcp.tool()
async def update_block(
    block_id: int,
    text: Optional[str] = None,
    template_type: Optional[str] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    w: Optional[int] = None,
) -> str:
    """更新現有 block 的內容或位置。只需傳入要修改的欄位。

    Args:
        block_id: 要更新的 Block ID
        text: 新的 markdown 內容
        template_type: 模板類型（link / image / list / todo / file）
        x: 新的水平位置
        y: 新的垂直位置
        w: 新的寬度
    """
    payload = {}
    if text is not None:
        payload["content"] = {"text": text}
    if template_type is not None:
        payload["template_type"] = template_type
    if x is not None:
        payload["x"] = x
    if y is not None:
        payload["y"] = y
    if w is not None:
        payload["w"] = w

    if not payload:
        return "沒有指定要更新的欄位。"

    data = await api("PUT", f"/api/blocks/{block_id}", json=payload)
    if data is None:
        return f"ERROR: 無法更新 block {block_id}"
    return f"Block {block_id} 更新成功。"


@mcp.tool()
async def delete_block(block_id: int) -> str:
    """刪除指定的 block。

    Args:
        block_id: 要刪除的 Block ID
    """
    data = await api("DELETE", f"/api/blocks/{block_id}")
    if data is None:
        return f"ERROR: 無法刪除 block {block_id}"
    return f"Block {block_id} 已刪除。"


@mcp.tool()
async def search_blocks(keyword: str) -> str:
    """搜尋所有專案中包含指定關鍵字的 blocks。

    Args:
        keyword: 要搜尋的關鍵字
    """
    projects = await api("GET", "/api/projects")
    if not projects:
        return "ERROR: 無法取得專案列表"

    results = []
    kw = keyword.lower()
    for p in projects:
        blocks = await api("GET", f"/api/projects/{p['id']}/blocks")
        if not blocks:
            continue
        for b in blocks:
            text = b.get("content", {}).get("text", "")
            if kw in text.lower():
                preview = text[:100].replace("\n", " ")
                results.append(
                    f"- block:{b['id']} in **{p['name']}** (project:{p['id']}, page:{b.get('page_id')})\n"
                    f"  {preview}"
                )

    if not results:
        return f"找不到包含「{keyword}」的 block。"
    return f"# 搜尋結果：「{keyword}」({len(results)} 筆)\n\n" + "\n".join(results)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
