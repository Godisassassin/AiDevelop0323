# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 知识切片存储服务

负责将处理好的切片和实体写入 MySQL 数据库，并更新 Redis 缓存。

Author: lhx
Date: 2026-04-24
"""

import json
import uuid
import logging
from typing import Optional

from common.db.database import SQLUnitOfWork
from common.db.redis import get_redis
from common.utils.base_entity_setting import add_setting

from app.service.wiki_knowledge.models.wiki_chunk import WikiChunk
from app.service.wiki_knowledge.models.global_kg import GlobalKG
from app.service.wiki_knowledge.models.alias_index import AliasIndex
from app.service.wiki_knowledge.models.chunk_map import ChunkMap


logger = logging.getLogger(__name__)


class WikiChunkStore:
    """知识切片存储器。

    封装 WikiChunk、GlobalKG、AliasIndex、ChunkMap 的写入逻辑。
    使用 SQLUnitOfWork 保证事务一致性。
    别名写入后自动更新 Redis 缓存。

    Methods:
        save_chunk: 保存切片
        save_kg: 保存知识节点
        save_alias: 保存别名（自动更新 Redis）
        save_chunk_map: 保存切片映射
        get_alias_candidates: 获取别名候选实体
    """

    # Redis 缓存配置
    REDIS_ALIAS_CACHE_KEY = "wiki:alias_index"
    REDIS_ALIAS_CACHE_TTL = 3600 * 24  # 24小时

    def save_chunk(
        self,
        chunk_id: str,
        doc_id: int,
        title_path: str,
        content: str,
        summary: Optional[str],
        parent_title: Optional[str],
        sibling_titles: list,
        user_id: Optional[str] = None,
    ) -> WikiChunk:
        """保存知识切片。

        Args:
            chunk_id: 切片唯一标识
            doc_id: 文档ID
            title_path: 标题路径
            content: 切片内容
            summary: 摘要
            parent_title: 父级标题
            sibling_titles: 同级标题列表
            user_id: 操作人ID（用于 BaseEntity 字段）

        Returns:
            WikiChunk 实例
        """
        wiki_chunk = WikiChunk()
        wiki_chunk.chunk_id = chunk_id
        wiki_chunk.doc_id = doc_id
        wiki_chunk.title_path = title_path
        wiki_chunk.content = content
        wiki_chunk.summary = summary
        wiki_chunk.parent_title = parent_title
        wiki_chunk.sibling_titles = (
            json.dumps(sibling_titles) if sibling_titles else None
        )

        if user_id:
            add_setting(wiki_chunk, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(wiki_chunk)

        return wiki_chunk

    def save_kg(
        self,
        standard_name: str,
        description: str,
        category: str,
        user_id: Optional[str] = None,
    ) -> str:
        """保存知识节点到 GlobalKG。

        Args:
            standard_name: 标准名称
            description: 实体定义
            category: 实体分类
            user_id: 操作人ID

        Returns:
            kg_id：新创建的知识节点ID
        """
        kg_id = str(uuid.uuid4())
        global_kg = GlobalKG()
        global_kg.kg_id = kg_id
        global_kg.standard_name = standard_name
        global_kg.description = description
        global_kg.category = category

        if user_id:
            add_setting(global_kg, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(global_kg)

        return kg_id

    def save_alias(
        self,
        alias_name: str,
        kg_id: str,
        pending_review: bool = False,
        user_id: Optional[str] = None,
    ) -> AliasIndex:
        """保存别名到 AliasIndex。

        Args:
            alias_name: 别名/同义词
            kg_id: 知识节点ID
            pending_review: 是否待审核（软关联）
            user_id: 操作人ID

        Returns:
            AliasIndex 实例
        """
        alias = AliasIndex()
        alias.alias_name = alias_name
        alias.kg_id = kg_id
        alias.pending_review = pending_review

        if user_id:
            add_setting(alias, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(alias)

        # 更新 Redis 缓存
        self._update_redis_cache(alias_name, kg_id, pending_review)

        return alias

    def save_chunk_map(
        self,
        chunk_id: str,
        kg_id: str,
        weight: float = 1.0,
        user_id: Optional[str] = None,
    ) -> ChunkMap:
        """保存切片与知识节点的映射。

        Args:
            chunk_id: 切片ID
            kg_id: 知识节点ID
            weight: 关联权重
            user_id: 操作人ID

        Returns:
            ChunkMap 实例
        """
        chunk_map = ChunkMap()
        chunk_map.chunk_id = chunk_id
        chunk_map.kg_id = kg_id
        chunk_map.weight = weight

        if user_id:
            add_setting(chunk_map, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(chunk_map)

        return chunk_map

    def get_alias_candidates(self, entity_name: str) -> list[dict]:
        """获取别名候选实体。

        优先从 Redis 缓存查询，缓存未命中时查询 MySQL。

        Args:
            entity_name: 实体名

        Returns:
            候选实体列表，每个包含 kg_id, name, description
        """
        # 尝试从 Redis 缓存获取
        redis_result = self._get_from_redis_cache(entity_name)
        if redis_result:
            return redis_result

        # 缓存未命中，查询 MySQL
        with SQLUnitOfWork() as uow:
            aliases = (
                uow.session.query(AliasIndex)
                .filter(
                    AliasIndex.alias_name == entity_name,
                    not AliasIndex.delete_flag,
                )
                .limit(10)
                .all()
            )

            if not aliases:
                return []

            # 获取关联的 GlobalKG 信息
            candidates = []
            for alias in aliases:
                kg = (
                    uow.session.query(GlobalKG)
                    .filter(GlobalKG.kg_id == alias.kg_id, not GlobalKG.delete_flag)
                    .first()
                )

                candidates.append(
                    {
                        "kg_id": alias.kg_id,
                        "name": alias.alias_name,
                        "description": kg.description if kg else "",
                    }
                )

            return candidates

    def _update_redis_cache(
        self, alias_name: str, kg_id: str, pending_review: bool
    ) -> None:
        """更新 Redis 缓存。

        Args:
            alias_name: 别名名称
            kg_id: 知识节点ID
            pending_review: 是否待审核
        """
        try:
            redis_client = get_redis()
            if not redis_client:
                return

            cache_data = {"kg_id": kg_id, "pending_review": str(pending_review)}
            redis_client.hset(
                self.REDIS_ALIAS_CACHE_KEY, alias_name, json.dumps(cache_data)
            )
            redis_client.expire(self.REDIS_ALIAS_CACHE_KEY, self.REDIS_ALIAS_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Redis 缓存更新失败: {e}")

    def _get_from_redis_cache(self, alias_name: str) -> Optional[list[dict]]:
        """从 Redis 缓存获取别名信息。

        Args:
            alias_name: 别名名称

        Returns:
            缓存的候选实体列表，未命中返回 None
        """
        try:
            redis_client = get_redis()
            if not redis_client:
                return None

            cached = redis_client.hget(self.REDIS_ALIAS_CACHE_KEY, alias_name)
            if cached:
                data = json.loads(cached)
                return [{"kg_id": data["kg_id"], "name": alias_name, "description": ""}]
        except Exception as e:
            logger.warning(f"Redis 缓存查询失败: {e}")

        return None
