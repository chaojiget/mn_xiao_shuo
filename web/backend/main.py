"""FastAPI 后端服务"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

# 添加项目根目录到路径
sys.path.insert(0, str(project_root))

from src.utils.database import Database
from src.models import WorldState, Character
from api.chat_api import router as chat_router
from api.generation_api import router as generation_router
from api.game_api import router as game_router, init_game_engine
from api.dm_api import router as dm_router, init_dm_agent
from llm import create_backend, get_available_backends
from llm.config_loader import LLMConfigLoader
from api.world_api import router as world_router, init_world_services
from database.world_db import WorldDatabase

app = FastAPI(title="AI 小说生成器 API")

# CORS 配置（必须在路由注册之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001"  # Next.js 备用端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册聊天路由
app.include_router(chat_router)

# 注册自动生成路由
app.include_router(generation_router)

# 注册游戏路由
app.include_router(game_router)

# 注册 DM Agent 路由
app.include_router(dm_router)

# 注册世界管理路由
app.include_router(world_router)

# 全局状态（延迟初始化）
llm_backend = None  # 改名为 llm_backend，使用新的抽象层
db = None
world_db = None


class NovelCreateRequest(BaseModel):
    """创建小说请求"""
    title: str
    novel_type: str  # scifi / xianxia
    preference: str = "hybrid"


class GenerateChapterRequest(BaseModel):
    """生成章节请求"""
    novel_id: str
    chapter_num: int
    user_choice: Optional[str] = None


@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global llm_backend, db, world_db

    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent

    # 初始化 LLM 后端（使用配置加载器）
    config_loader = LLMConfigLoader()
    backend_type = config_loader.get_backend_type()
    backend_config = config_loader.get_backend_config()

    # 打印配置摘要
    config_loader.print_config_summary()

    # 创建后端实例
    llm_backend = create_backend(backend_type, backend_config)
    print(f"✅ LLM 后端已初始化 (类型: {backend_type})")

    # 打印后端信息
    backend_info = llm_backend.get_backend_info()
    print(f"   - 后端: {backend_info.get('backend', 'unknown')}")
    print(f"   - 模型: {backend_info.get('model', 'unknown')}")

    # 初始化数据库
    db_path = project_root / "data" / "sqlite" / "novel.db"
    db = Database(db_path=str(db_path))
    db.connect()
    print(f"✅ 数据库已连接 (路径: {db_path})")

    # 初始化世界数据库
    world_db = WorldDatabase(db_path=str(db_path))
    print(f"✅ 世界数据库已初始化")

    # 初始化游戏引擎（传入后端实例和数据库路径）
    init_game_engine(llm_backend, db_path=str(db_path))
    print(f"✅ 游戏引擎已初始化")

    # 初始化世界服务
    init_world_services(world_db, llm_backend)
    print(f"✅ 世界管理服务已初始化")

    # 初始化 DM Agent
    init_dm_agent()
    print(f"✅ DM Agent 已初始化")


@app.on_event("shutdown")
async def shutdown():
    """关闭时清理"""
    if db:
        db.close()
        print("👋 数据库已关闭")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI 小说生成器 API", "status": "running"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"message": "OK", "status": "running"}


@app.get("/api/novels")
async def list_novels():
    """获取所有小说列表"""
    # TODO: 实现数据库查询
    return {
        "novels": [
            {
                "id": "novel_001",
                "title": "能源纪元",
                "type": "scifi",
                "chapters": 15,
                "created_at": "2025-10-30"
            }
        ]
    }


@app.post("/api/novels")
async def create_novel(request: NovelCreateRequest):
    """创建新小说"""
    import uuid

    novel_id = f"novel_{uuid.uuid4().hex[:8]}"

    # TODO: 保存到数据库
    db.create_novel(
        novel_id=novel_id,
        title=request.title,
        novel_type=request.novel_type,
        setting_json={},  # 从模板加载
        preference=request.preference
    )

    return {
        "novel_id": novel_id,
        "title": request.title,
        "type": request.novel_type
    }


@app.websocket("/ws/generate/{novel_id}")
async def websocket_generate(websocket: WebSocket, novel_id: str):
    """WebSocket 实时生成章节"""
    await websocket.accept()

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()

            chapter_num = data.get("chapter_num", 1)
            user_choice = data.get("user_choice")

            # 发送生成中状态
            await websocket.send_json({
                "type": "status",
                "status": "generating",
                "chapter_num": chapter_num
            })

            # 生成章节内容
            prompt = f"生成第 {chapter_num} 章内容"
            if user_choice:
                prompt += f"\\n\\n用户选择: {user_choice}"

            try:
                # 使用新的后端抽象层
                from llm.base import LLMMessage
                messages = [LLMMessage(role="user", content=prompt)]
                response = await llm_backend.generate(
                    messages=messages,
                    temperature=0.8,
                    max_tokens=2000
                )
                content = response.content

                # 保存章节
                db.save_chapter(
                    novel_id=novel_id,
                    chapter_num=chapter_num,
                    content=content
                )

                # 发送生成完成
                await websocket.send_json({
                    "type": "chapter",
                    "chapter_num": chapter_num,
                    "content": content,
                    "word_count": len(content)
                })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        print(f"客户端断开连接: {novel_id}")


@app.get("/api/novels/{novel_id}")
async def get_novel(novel_id: str):
    """获取小说详情"""
    novel = db.get_novel(novel_id)
    if not novel:
        return {"error": "小说不存在"}

    chapters = db.get_all_chapters(novel_id)
    stats = db.get_stats(novel_id)

    return {
        "novel": novel,
        "chapters": chapters,
        "stats": stats
    }


@app.get("/api/novels/{novel_id}/chapters/{chapter_num}")
async def get_chapter(novel_id: str, chapter_num: int):
    """获取指定章节"""
    chapter = db.get_chapter(novel_id, chapter_num)
    return chapter or {"error": "章节不存在"}


@app.get("/api/novels/{novel_id}/export")
async def export_novel(novel_id: str):
    """导出小说为 Markdown"""
    novel = db.get_novel(novel_id)
    chapters = db.get_all_chapters(novel_id)

    markdown = f"# {novel['title']}\\n\\n"
    for chapter in chapters:
        markdown += f"## 第 {chapter['chapter_num']} 章\\n\\n"
        markdown += f"{chapter['content']}\\n\\n---\\n\\n"

    return {"markdown": markdown}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
