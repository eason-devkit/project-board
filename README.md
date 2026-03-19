## Project Board

剪貼簿形式的專案資訊管理工具。以區塊（Block）為單位，在看板上自由排列 Markdown 筆記、連結、圖片等內容。

### 技術架構

| 層級 | 技術 |
|------|------|
| 前端 | Vue 3, Tailwind CSS v4, Pinia, Vite |
| 後端 | FastAPI, SQLAlchemy, Pydantic |
| 資料庫 | SQLite |

### 功能概覽

- 專案管理（建立、編輯、標籤分類）
- 多頁面支援（每個專案可建立多個頁面）
- 區塊編輯（Markdown 編輯器、即時預覽）
- 自由排版（拖曳移動、調整大小）
- 檔案上傳（圖片、文件）
- 區塊模板（快速套用預設格式）
- MCP Server 整合（供 AI 工具直接操作看板）

### 快速開始

需要 Python 3 和 Node.js。

```bash
# 建立虛擬環境並安裝後端依賴
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -r backend/requirements.txt

# 安裝前端依賴
cd frontend && npm install && cd ..

# 啟動（同時開啟前後端）
python run.py
```

前端：http://localhost:5173，後端 API：http://localhost:8001/docs

### 專案結構

```
├── frontend/             # Vue 3 SPA
│   └── src/
│       ├── components/   # 區塊卡片、編輯器、模板對話框
│       ├── pages/        # 專案列表、看板頁面
│       ├── stores/       # Pinia 狀態管理
│       └── api/          # API 呼叫
├── backend/              # FastAPI 應用
│   ├── main.py           # API 路由與啟動
│   ├── models.py         # SQLAlchemy 資料模型
│   ├── schemas.py        # Pydantic schemas
│   ├── mcp_server.py     # MCP Server
│   └── uploads/          # 上傳檔案存放
└── run.py                # 一鍵啟動腳本
```
