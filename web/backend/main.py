"""FastAPI 后端服务 - 主入口

使用统一的配置管理、日志系统和错误处理。
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 添加项目根目录到路径（必须在导入其他模块之前）
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载 .env 文件
load_dotenv(project_root / ".env")

# 导入统一的配置和工具
from config.settings import settings

from utils.exceptions import AppException, handle_exception
from utils.logger import get_logger, setup_logging

# 初始化日志系统（应该在所有其他导入之前）
setup_logging(log_level=settings.log_level, log_file=settings.log_file)
logger = get_logger(__name__)

from api.dm_api import init_dm_agent
from api.dm_api import router as dm_router
from api.game_api import init_game_engine
from api.game_api import router as game_router
from api.worlds_api import router as worlds_router
from database.world_db import WorldDatabase

from llm import create_backend, get_available_backends
from llm.config_loader import LLMConfigLoader
from src.models import Character, WorldState

# 导入业务模块
from src.utils.database import Database

# 创建 FastAPI 应用
app = FastAPI(
    title="AI 小说生成器 API",
    version="1.0.0",
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理自定义应用异常"""
    logger.error(f"应用异常: {exc.message}", exc_info=True)
    return JSONResponse(status_code=400, content=exc.to_dict())


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content=handle_exception(exc))


# 注册游戏路由
app.include_router(game_router)

# 注册 DM Agent 路由
app.include_router(dm_router)

# 注册世界包管理路由
app.include_router(worlds_router)

# 全局状态（延迟初始化）
llm_backend = None
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
    """启动时初始化所有组件"""
    global llm_backend, db, world_db

    logger.info("========================================")
    logger.info("🚀 启动 AI 小说生成器后端服务")
    logger.info("========================================")

    try:
        # 1. 初始化 LLM 后端
        logger.info("初始化 LLM 后端...")
        config_loader = LLMConfigLoader()
        backend_type = config_loader.get_backend_type()
        backend_config = config_loader.get_backend_config()

        config_loader.print_config_summary()

        llm_backend = create_backend(backend_type, backend_config)
        backend_info = llm_backend.get_backend_info()

        logger.info(f"✅ LLM 后端已初始化")
        logger.info(f"   - 类型: {backend_type}")
        logger.info(f"   - 模型: {backend_info.get('model', 'unknown')}")

        # 2. 初始化数据库
        logger.info("初始化数据库...")
        db_path = settings.database_path
        db = Database(db_path=str(db_path))
        db.connect()
        logger.info(f"✅ 数据库已连接: {db_path}")

        # 3. 初始化世界数据库
        logger.info("初始化世界数据库...")
        world_db = WorldDatabase(db_path=str(db_path))
        logger.info("✅ 世界数据库已初始化")

        # 4. 初始化游戏引擎
        logger.info("初始化游戏引擎...")
        init_game_engine(llm_backend, db_path=str(db_path))
        logger.info("✅ 游戏引擎已初始化")

        # 5. 初始化 DM Agent
        logger.info("初始化 DM Agent...")
        init_dm_agent()
        logger.info("✅ DM Agent 已初始化")

        logger.info("========================================")
        logger.info(f"✅ 后端服务已启动")
        logger.info(f"   - 地址: http://{settings.backend_host}:{settings.backend_port}")
        logger.info(f"   - API 文档: http://{settings.backend_host}:{settings.backend_port}/docs")
        logger.info("========================================")

    except Exception as e:
        logger.critical(f"❌ 启动失败: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown():
    """关闭时清理资源"""
    logger.info("========================================")
    logger.info("👋 关闭后端服务...")
    logger.info("========================================")

    try:
        if db:
            db.close()
            logger.info("✅ 数据库已关闭")

        logger.info("✅ 所有资源已清理")

    except Exception as e:
        logger.error(f"❌ 关闭时发生错误: {e}", exc_info=True)


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
                "created_at": "2025-10-30",
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
        preference=request.preference,
    )

    return {"novel_id": novel_id, "title": request.title, "type": request.novel_type}


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
            await websocket.send_json(
                {"type": "status", "status": "generating", "chapter_num": chapter_num}
            )

            # 生成章节内容
            prompt = f"生成第 {chapter_num} 章内容"
            if user_choice:
                prompt += f"\\n\\n用户选择: {user_choice}"

            try:
                # 使用新的后端抽象层
                from llm.base import LLMMessage

                messages = [LLMMessage(role="user", content=prompt)]
                response = await llm_backend.generate(
                    messages=messages, temperature=0.8, max_tokens=2000
                )
                content = response.content

                # 保存章节
                db.save_chapter(novel_id=novel_id, chapter_num=chapter_num, content=content)

                # 发送生成完成
                await websocket.send_json(
                    {
                        "type": "chapter",
                        "chapter_num": chapter_num,
                        "content": content,
                        "word_count": len(content),
                    }
                )

            except Exception as e:
                logger.error(f"章节生成错误: {e}", exc_info=True)
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info(f"客户端断开连接: {novel_id}")


@app.get("/api/novels/{novel_id}")
async def get_novel(novel_id: str):
    """获取小说详情"""
    novel = db.get_novel(novel_id)
    if not novel:
        return {"error": "小说不存在"}

    chapters = db.get_all_chapters(novel_id)
    stats = db.get_stats(novel_id)

    return {"novel": novel, "chapters": chapters, "stats": stats}


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
