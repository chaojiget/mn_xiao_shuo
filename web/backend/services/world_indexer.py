"""
世界知识库索引器
为 NPC 和 Lore 构建轻量级向量索引，用于语义搜索和 RAG
"""

import json
import sqlite3
import pickle
from typing import List, Dict, Tuple, Optional
import numpy as np

from models.world_pack import WorldPack, NPC


class WorldIndexer:
    """世界知识库索引器（轻量级实现）"""

    def __init__(self, db_path: str, llm_client=None):
        """
        初始化索引器

        Args:
            db_path: 数据库路径
            llm_client: LLM 客户端（用于生成嵌入）
        """
        self.db_path = db_path
        self.llm = llm_client

    async def build_index(self, world_pack: WorldPack) -> Dict[str, int]:
        """
        构建完整的世界知识库索引

        Args:
            world_pack: 世界包

        Returns:
            Dict[str, int]: 统计信息
        """
        stats = {
            "npc_count": 0,
            "lore_count": 0,
            "total_embeddings": 0
        }

        # 清理旧索引
        self._clear_index(world_pack.meta.id)

        # 1. 索引 NPC
        npc_count = await self._index_npcs(world_pack)
        stats["npc_count"] = npc_count

        # 2. 索引 Lore
        lore_count = await self._index_lore(world_pack)
        stats["lore_count"] = lore_count

        stats["total_embeddings"] = npc_count + lore_count

        print(f"[WorldIndexer] ✅ 索引构建完成: {stats['total_embeddings']} 条记录")
        return stats

    async def _index_npcs(self, world_pack: WorldPack) -> int:
        """索引所有 NPC"""
        count = 0

        for npc in world_pack.npcs:
            # 构建 NPC 文本
            text = self._build_npc_text(npc)

            # 生成嵌入
            embedding = await self._get_embedding(text)

            # 保存到数据库
            self._save_embedding(
                world_id=world_pack.meta.id,
                kind="npc",
                ref_id=npc.id,
                content=text,
                embedding=embedding
            )

            count += 1

        print(f"[WorldIndexer] 索引了 {count} 个 NPC")
        return count

    async def _index_lore(self, world_pack: WorldPack) -> int:
        """索引所有 Lore 条目"""
        count = 0

        for key, text in world_pack.lore.items():
            # 生成嵌入
            embedding = await self._get_embedding(text)

            # 保存到数据库
            self._save_embedding(
                world_id=world_pack.meta.id,
                kind="lore",
                ref_id=key,
                content=text,
                embedding=embedding
            )

            count += 1

        print(f"[WorldIndexer] 索引了 {count} 个 Lore 条目")
        return count

    def _build_npc_text(self, npc: NPC) -> str:
        """构建 NPC 的索引文本"""
        parts = [
            f"名字: {npc.name}",
            f"角色: {npc.role}",
            f"性格: {npc.persona}",
        ]

        if npc.desires:
            parts.append(f"欲望: {', '.join(npc.desires)}")

        if npc.secrets:
            parts.append(f"秘密: {', '.join(npc.secrets)}")

        return "\n".join(parts)

    async def _get_embedding(self, text: str) -> np.ndarray:
        """
        生成文本嵌入

        使用简单的方法：如果没有 LLM 客户端，使用哈希值模拟
        在实际使用中应该调用 OpenAI Embeddings API
        """
        if self.llm is None:
            # 简单的哈希向量（测试用）
            import hashlib
            hash_obj = hashlib.md5(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            # 转换为 128 维向量
            vector = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
            # 归一化
            vector = vector / np.linalg.norm(vector)
            return vector
        else:
            # TODO: 调用 OpenAI Embeddings API
            # embedding = await self.llm.get_embedding(text)
            # return np.array(embedding)

            # 暂时使用哈希向量
            import hashlib
            hash_obj = hashlib.md5(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            vector = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
            vector = vector / np.linalg.norm(vector)
            return vector

    def _save_embedding(
        self,
        world_id: str,
        kind: str,
        ref_id: str,
        content: str,
        embedding: np.ndarray
    ):
        """保存嵌入到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 序列化嵌入向量
            embedding_blob = pickle.dumps(embedding)

            # 生成唯一 ID
            kb_id = f"{world_id}:{kind}:{ref_id}"

            cursor.execute("""
                INSERT INTO world_kb (id, world_id, kind, ref_id, content, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    content = excluded.content,
                    embedding = excluded.embedding
            """, (kb_id, world_id, kind, ref_id, content, embedding_blob))

            conn.commit()

        finally:
            conn.close()

    def _clear_index(self, world_id: str):
        """清理指定世界的索引"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM world_kb WHERE world_id = ?", (world_id,))
            conn.commit()
            print(f"[WorldIndexer] 清理了世界 {world_id} 的旧索引")

        finally:
            conn.close()

    def search(
        self,
        world_id: str,
        query: str,
        kind: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        语义搜索

        Args:
            world_id: 世界 ID
            query: 查询文本
            kind: 类型过滤（npc/lore）
            top_k: 返回结果数

        Returns:
            List[Dict]: 搜索结果 [{"ref_id": ..., "content": ..., "score": ...}]
        """
        # 生成查询嵌入
        import asyncio
        query_embedding = asyncio.run(self._get_embedding(query))

        # 从数据库加载所有嵌入
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if kind:
                cursor.execute("""
                    SELECT ref_id, content, embedding
                    FROM world_kb
                    WHERE world_id = ? AND kind = ?
                """, (world_id, kind))
            else:
                cursor.execute("""
                    SELECT ref_id, content, embedding
                    FROM world_kb
                    WHERE world_id = ?
                """, (world_id,))

            results = []
            for row in cursor.fetchall():
                ref_id, content, embedding_blob = row

                # 反序列化嵌入
                embedding = pickle.loads(embedding_blob)

                # 计算余弦相似度
                score = self._cosine_similarity(query_embedding, embedding)

                results.append({
                    "ref_id": ref_id,
                    "content": content,
                    "score": float(score)
                })

            # 按分数排序
            results.sort(key=lambda x: x["score"], reverse=True)

            return results[:top_k]

        finally:
            conn.close()

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get_npc_context(
        self,
        world_id: str,
        npc_id: str,
        recent_events: List[str] = []
    ) -> str:
        """
        获取 NPC 的上下文（用于对话）

        Args:
            world_id: 世界 ID
            npc_id: NPC ID
            recent_events: 近期事件列表

        Returns:
            str: NPC 上下文文本
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 获取 NPC 基础信息
            cursor.execute("""
                SELECT content FROM world_kb
                WHERE world_id = ? AND kind = 'npc' AND ref_id = ?
            """, (world_id, npc_id))

            row = cursor.fetchone()
            if not row:
                return f"NPC {npc_id} 信息未找到"

            npc_info = row[0]

            # 构建上下文
            context_parts = [
                "=== NPC 基础信息 ===",
                npc_info
            ]

            # 添加近期事件
            if recent_events:
                context_parts.append("\n=== 近期事件 ===")
                for event in recent_events[-5:]:  # 最近 5 个事件
                    context_parts.append(f"- {event}")

            return "\n".join(context_parts)

        finally:
            conn.close()

    def get_relevant_lore(
        self,
        world_id: str,
        context: str,
        top_k: int = 3
    ) -> List[str]:
        """
        获取相关的 Lore 条目（RAG）

        Args:
            world_id: 世界 ID
            context: 当前上下文
            top_k: 返回数量

        Returns:
            List[str]: Lore 文本列表
        """
        results = self.search(
            world_id=world_id,
            query=context,
            kind="lore",
            top_k=top_k
        )

        return [r["content"] for r in results]

    def get_stats(self, world_id: str) -> Dict[str, int]:
        """获取索引统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT kind, COUNT(*) as count
                FROM world_kb
                WHERE world_id = ?
                GROUP BY kind
            """, (world_id,))

            stats = {"total": 0}
            for row in cursor.fetchall():
                kind, count = row
                stats[kind] = count
                stats["total"] += count

            return stats

        finally:
            conn.close()


# 工厂函数
def create_world_indexer(db_path: str, llm_client=None) -> WorldIndexer:
    """
    创建世界索引器

    Args:
        db_path: 数据库路径
        llm_client: LLM 客户端（可选）

    Returns:
        WorldIndexer: 索引器实例
    """
    return WorldIndexer(db_path, llm_client)
