# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 多路精准匹配器

通过路径匹配和实体导航两路并发检索切片，合并结果返回。

Author: lhx
Date: 2026-04-27
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from common.db.database import SQLUnitOfWork

from app.service.wiki_knowledge.models.wiki_chunk import WikiChunk
from app.service.wiki_knowledge.models.chunk_map import ChunkMap
from app.service.wiki_knowledge.models.alias_index import AliasIndex
from app.service.wiki_knowledge.models.global_kg import GlobalKG
from app.service.wiki_knowledge.processor.chunk_store import WikiChunkStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalCandidate:
    """检索候选切片。

    Attributes:
        chunk_id: 切片唯一标识
        title_path: 标题路径
        content: 切片内容
        score: 匹配分数
        match_type: 匹配类型（path_match / entity_navigate）
    """
    chunk_id: str
    title_path: str
    content: str
    score: float
    match_type: str = "path_match"


class MultiMatchRetriever:
    """多路精准匹配器。

    通过两路并发检索切片：
    1. 路径匹配：通过 title_path 模糊匹配目标实体
    2. 实体导航：通过 alias_index 找到 kg_id，再通过 chunk_map 找到关联切片

    Methods:
        retrieve: 执行多路检索
        _path_match: 路径匹配
        _entity_navigate: 实体导航
        _merge_results: 合并去重结果
    """

    def __init__(self):
        """初始化匹配器。"""
        self.store = WikiChunkStore()

    async def retrieve(
        self,
        target: str,
        action: str,
        knowledge_ids: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[RetrievalCandidate]:
        """执行多路检索。

        Args:
            target: 目标实体
            action: 动作词
            knowledge_ids: 知识库ID列表（可选，用于过滤）
            limit: 返回结果数量限制

        Returns:
            检索候选切片列表，按分数降序排列
        """
        # 并发执行两路检索
        path_results = await self._path_match(target, knowledge_ids)
        entity_results = await self._entity_navigate(target, knowledge_ids)

        # 合并结果
        merged = self._merge_results(path_results, entity_results)

        # 按分数排序并限制数量
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:limit]

    async def _path_match(
        self,
        target: str,
        knowledge_ids: Optional[list[str]] = None,
    ) -> list[RetrievalCandidate]:
        """路径匹配。

        通过 title_path 模糊匹配目标实体。

        Args:
            target: 目标实体
            knowledge_ids: 知识库ID列表

        Returns:
            匹配的切片列表
        """
        results = []
        try:
            with SQLUnitOfWork() as uow:
                # 构建模糊查询条件
                # title_path 包含 target 的切片
                query = uow.session.query(WikiChunk).filter(
                    WikiChunk.title_path.contains(target),
                    not WikiChunk.delete_flag,
                )

                # 如果指定了 knowledge_ids，进行过滤
                # 注意：WikiChunk 有 doc_id，需要通过其他方式关联 knowledge
                # 此处暂时不添加 knowledge_ids 过滤，后续通过 chunk_map 关联

                chunks = query.limit(50).all()

                for chunk in chunks:
                    # 计算匹配分数：基于 title_path 中 target 的位置和长度
                    score = self._calculate_path_score(chunk.title_path, target)
                    results.append(
                        RetrievalCandidate(
                            chunk_id=chunk.chunk_id,
                            title_path=chunk.title_path,
                            content=chunk.content,
                            score=score,
                            match_type="path_match",
                        )
                    )

        except Exception as e:
            logger.warning(f"路径匹配查询失败: {e}")

        return results

    async def _entity_navigate(
        self,
        target: str,
        knowledge_ids: Optional[list[str]] = None,
    ) -> list[RetrievalCandidate]:
        """实体导航。

        通过 alias_index 找到 kg_id，再通过 chunk_map 找到关联切片。

        Args:
            target: 目标实体
            knowledge_ids: 知识库ID列表

        Returns:
            匹配的切片列表
        """
        results = []

        # 通过 WikiChunkStore 获取别名候选实体
        candidates = self.store.get_alias_candidates(target)

        if not candidates:
            return results

        try:
            with SQLUnitOfWork() as uow:
                for candidate in candidates:
                    kg_id = candidate["kg_id"]

                    # 通过 chunk_map 找到关联的切片
                    chunk_maps = (
                        uow.session.query(ChunkMap)
                        .filter(
                            ChunkMap.kg_id == kg_id,
                            not ChunkMap.delete_flag,
                        )
                        .all()
                    )

                    for chunk_map in chunk_maps:
                        # 获取切片详情
                        chunk = (
                            uow.session.query(WikiChunk)
                            .filter(
                                WikiChunk.chunk_id == chunk_map.chunk_id,
                                not WikiChunk.delete_flag,
                            )
                            .first()
                        )

                        if chunk:
                            results.append(
                                RetrievalCandidate(
                                    chunk_id=chunk.chunk_id,
                                    title_path=chunk.title_path,
                                    content=chunk.content,
                                    score=chunk_map.weight,
                                    match_type="entity_navigate",
                                )
                            )

        except Exception as e:
            logger.warning(f"实体导航查询失败: {e}")

        return results

    def _merge_results(
        self,
        path_results: list[RetrievalCandidate],
        entity_results: list[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:
        """合并去重结果。

        对于同一个 chunk_id，保留最高分数的结果。

        Args:
            path_results: 路径匹配结果
            entity_results: 实体导航结果

        Returns:
            合并去重后的结果列表
        """
        merged_dict: dict[str, RetrievalCandidate] = {}

        # 添加路径匹配结果
        for candidate in path_results:
            if candidate.chunk_id not in merged_dict:
                merged_dict[candidate.chunk_id] = candidate
            elif candidate.score > merged_dict[candidate.chunk_id].score:
                merged_dict[candidate.chunk_id] = candidate

        # 添加实体导航结果
        for candidate in entity_results:
            if candidate.chunk_id not in merged_dict:
                merged_dict[candidate.chunk_id] = candidate
            elif candidate.score > merged_dict[candidate.chunk_id].score:
                merged_dict[candidate.chunk_id] = candidate

        return list(merged_dict.values())

    def _calculate_path_score(self, title_path: str, target: str) -> float:
        """计算路径匹配分数。

        基于 target 在 title_path 中的位置和匹配程度计算分数。

        Args:
            title_path: 标题路径
            target: 目标实体

        Returns:
            匹配分数 (0-1)
        """
        if not title_path or not target:
            return 0.0

        # 完全匹配
        if target in title_path:
            # 根据匹配位置调整分数
            # 标题开头匹配权重更高
            if title_path.startswith(target):
                return 1.0
            elif f" > {target}" in title_path or f">{target}" in title_path:
                return 0.9
            else:
                return 0.7

        # 部分匹配（简单的包含检查）
        target_lower = target.lower()
        path_lower = title_path.lower()
        if target_lower in path_lower:
            return 0.5

        return 0.0