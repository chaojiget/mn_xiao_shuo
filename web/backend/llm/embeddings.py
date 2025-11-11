"""
Embedding Provider - OpenRouter (Qwen) 优先，失败回退哈希向量。

默认模型：settings.embedding_model 或 qwen/qwen3-embedding-8b
"""

from __future__ import annotations

import hashlib
from typing import List

import numpy as np
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    from langchain_openai import OpenAIEmbeddings
    _LC_EMB_OK = True
except Exception:
    _LC_EMB_OK = False


class EmbeddingClient:
    def __init__(self, model: str | None = None):
        self.model = model or getattr(settings, "embedding_model", None) or "qwen/qwen3-embedding-8b"
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key

        if not _LC_EMB_OK:
            logger.warning("langchain_openai.OpenAIEmbeddings 不可用，将在失败时回退哈希向量")

        self._emb = None
        if _LC_EMB_OK and self.api_key:
            try:
                self._emb = OpenAIEmbeddings(model=self.model, base_url=self.base_url, api_key=self.api_key)
                logger.info(f"[Embeddings] 使用 OpenRouter embeddings: {self.model}")
            except Exception as e:
                logger.warning(f"[Embeddings] 初始化失败，回退哈希向量: {e}")
                self._emb = None

    def _hash_vec(self, text: str) -> np.ndarray:
        h = hashlib.md5(text.encode("utf-8")).digest()
        v = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
        v = v / np.linalg.norm(v)
        return v

    def embed_text(self, text: str) -> np.ndarray:
        if self._emb is None:
            return self._hash_vec(text)
        try:
            vec = self._emb.embed_query(text)
            arr = np.array(vec, dtype=np.float32)
            # 归一化（与索引一致）
            if np.linalg.norm(arr) > 0:
                arr = arr / np.linalg.norm(arr)
            return arr
        except Exception as e:
            logger.warning(f"[Embeddings] 同步嵌入失败，回退哈希: {e}")
            return self._hash_vec(text)

    async def aembed_text(self, text: str) -> np.ndarray:
        # OpenAIEmbeddings 无 aio 接口，这里同步调用即可
        return self.embed_text(text)

    async def aembed_texts(self, texts: List[str]) -> List[np.ndarray]:
        return [self.embed_text(t) for t in texts]

