"""
会话历史管理
Conversation History Management

功能:
1. 记录用户与系统的完整对话
2. 支持历史回顾和上下文恢复
3. 支持分支对话管理
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from uuid import uuid4


class Message(BaseModel):
    """单条消息"""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # 附加数据（如生成参数、选择等）
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # 消息类型
    message_type: Optional[Literal["text", "choice", "setting_edit", "chapter", "npc_generated"]] = "text"


class ConversationBranch(BaseModel):
    """对话分支（支持多条探索路径）"""
    branch_id: str = Field(default_factory=lambda: str(uuid4()))
    branch_name: str = "主分支"
    parent_message_id: Optional[str] = None  # 从哪条消息分支出来

    # 消息列表
    messages: List[Message] = Field(default_factory=list)

    # 分支元信息
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

    def add_message(
        self,
        role: Literal["user", "assistant", "system"],
        content: str,
        message_type: Optional[str] = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """添加消息到分支"""
        message = Message(
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        self.messages.append(message)
        return message

    def get_recent_messages(self, n: int = 10) -> List[Message]:
        """获取最近N条消息"""
        return self.messages[-n:]

    def get_context_window(self, max_tokens: int = 4000) -> List[Message]:
        """获取上下文窗口（按token估算）"""
        result = []
        total_tokens = 0

        # 从后往前遍历
        for message in reversed(self.messages):
            # 粗略估算：中文1字≈2token，英文1词≈1.3token
            estimated_tokens = len(message.content) * 2
            if total_tokens + estimated_tokens > max_tokens:
                break
            result.insert(0, message)
            total_tokens += estimated_tokens

        return result


class ConversationSession(BaseModel):
    """完整会话（支持多分支）"""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    novel_id: str  # 关联的小说ID

    # 分支管理
    branches: Dict[str, ConversationBranch] = Field(default_factory=dict)
    active_branch_id: str  # 当前活跃分支

    # 会话元信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 会话摘要（可选）
    summary: str = ""

    def __init__(self, **data):
        if "branches" not in data or not data["branches"]:
            # 创建默认主分支
            main_branch = ConversationBranch(branch_name="主分支")
            data["branches"] = {main_branch.branch_id: main_branch}
            data["active_branch_id"] = main_branch.branch_id
        super().__init__(**data)

    def get_active_branch(self) -> ConversationBranch:
        """获取当前活跃分支"""
        return self.branches[self.active_branch_id]

    def add_message(
        self,
        role: Literal["user", "assistant", "system"],
        content: str,
        message_type: Optional[str] = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """添加消息到当前活跃分支"""
        branch = self.get_active_branch()
        message = branch.add_message(role, content, message_type, metadata)
        self.updated_at = datetime.now()
        return message

    def create_branch(
        self,
        branch_name: str,
        from_message_id: Optional[str] = None
    ) -> ConversationBranch:
        """创建新分支"""
        new_branch = ConversationBranch(
            branch_name=branch_name,
            parent_message_id=from_message_id
        )

        # 如果指定了父消息，复制父消息之前的所有消息
        if from_message_id:
            active_branch = self.get_active_branch()
            for msg in active_branch.messages:
                new_branch.messages.append(msg.model_copy(deep=True))
                if msg.message_id == from_message_id:
                    break

        self.branches[new_branch.branch_id] = new_branch
        return new_branch

    def switch_branch(self, branch_id: str):
        """切换活跃分支"""
        if branch_id in self.branches:
            self.active_branch_id = branch_id
            self.updated_at = datetime.now()

    def get_all_branches_summary(self) -> List[Dict[str, Any]]:
        """获取所有分支摘要"""
        return [
            {
                "branch_id": branch.branch_id,
                "branch_name": branch.branch_name,
                "message_count": len(branch.messages),
                "created_at": branch.created_at,
                "is_active": branch.branch_id == self.active_branch_id
            }
            for branch in self.branches.values()
        ]

    def get_conversation_history(
        self,
        branch_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """获取对话历史"""
        if branch_id:
            branch = self.branches.get(branch_id)
        else:
            branch = self.get_active_branch()

        if not branch:
            return []

        messages = branch.messages
        if limit:
            messages = messages[-limit:]

        return messages

    def export_to_markdown(self, branch_id: Optional[str] = None) -> str:
        """导出对话历史为Markdown格式"""
        messages = self.get_conversation_history(branch_id)

        lines = [
            f"# 对话历史 - {self.novel_id}",
            f"**会话ID**: {self.session_id}",
            f"**创建时间**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]

        for msg in messages:
            role_name = {
                "user": "👤 用户",
                "assistant": "🤖 助手",
                "system": "⚙️ 系统"
            }.get(msg.role, msg.role)

            timestamp = msg.timestamp.strftime("%H:%M:%S")

            lines.append(f"## {role_name} [{timestamp}]")
            lines.append("")
            lines.append(msg.content)
            lines.append("")

            if msg.metadata:
                lines.append("**元数据**:")
                lines.append(f"```json\n{msg.metadata}\n```")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


class ConversationManager(BaseModel):
    """会话管理器（管理多个小说的会话）"""
    sessions: Dict[str, ConversationSession] = Field(default_factory=dict)

    def create_session(self, novel_id: str) -> ConversationSession:
        """为小说创建新会话"""
        session = ConversationSession(novel_id=novel_id)
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """获取会话"""
        return self.sessions.get(session_id)

    def get_sessions_by_novel(self, novel_id: str) -> List[ConversationSession]:
        """获取某个小说的所有会话"""
        return [
            session for session in self.sessions.values()
            if session.novel_id == novel_id
        ]

    def delete_session(self, session_id: str):
        """删除会话"""
        self.sessions.pop(session_id, None)
