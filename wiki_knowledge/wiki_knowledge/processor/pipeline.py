# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 文档入库流水线入口

整合切片处理、特征提取、实体对齐和存储的完整流程。

Author: lhx
Date: 2026-04-27
"""

from typing import Optional

from app.service.wiki_knowledge.processor.chunk_processor import (
    WikiChunkProcessor,
    ChunkResult,
)
from app.service.wiki_knowledge.processor.context_extractor import (
    ContextAwareExtractor,
    ExtractionResult,
)
from app.service.wiki_knowledge.processor.entity_resolver import (
    EntityResolver,
    ResolutionResult,
    ResolutionType,
)
from app.service.wiki_knowledge.processor.chunk_store import WikiChunkStore


class WikiKnowledgePipeline:
    """Wiki 知识库文档入库流水线。

    整合切片处理、特征提取、实体对齐和存储。

    Methods:
        process_document: 处理文档并入库
    """

    def __init__(self):
        """初始化流水线各组件。"""
        self.processor = WikiChunkProcessor()
        self.extractor = ContextAwareExtractor()
        self.resolver = EntityResolver()
        self.store = WikiChunkStore()

    async def process_document(
        self,
        markdown_content: str,
        doc_id: int,
        knowledge_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """处理文档并入库。

        Args:
            markdown_content: Markdown 格式的文档内容
            doc_id: 文档唯一标识
            knowledge_id: 知识库ID（可选，用于关联）
            user_id: 操作人ID

        Returns:
            处理结果统计（chunks, entities, alias, new_kg）
        """
        # Step 1: 切片处理
        chunks = self.processor.process(markdown_content, doc_id)

        # 统计结果
        stats = {"chunks": 0, "entities": 0, "alias": 0, "new_kg": 0}

        # Step 2: 遍历切片进行特征提取和实体对齐
        for chunk in chunks:
            # 保存切片
            self.store.save_chunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                title_path=chunk.title_path,
                content=chunk.content,
                summary=chunk.summary,
                parent_title=chunk.parent_title,
                sibling_titles=chunk.sibling_titles,
                user_id=user_id,
            )
            stats["chunks"] += 1

            # 特征提取
            extraction = await self.extractor.extract(chunk)

            # 实体对齐与存储
            for entity in extraction.entities + extraction.concepts:
                # 候选筛选
                candidates = self.store.get_alias_candidates(entity)

                # LLM 裁决
                resolution = await self.resolver.resolve(
                    entity_name=entity,
                    entity_def=chunk.content[:500],
                    candidates=candidates,
                )

                # 根据裁决结果处理
                if resolution.resolution_type == ResolutionType.NEW:
                    # 创建新知识节点
                    kg_id = self.store.save_kg(
                        standard_name=entity,
                        description=chunk.content[:200],
                        category="entity" if entity in extraction.entities else "concept",
                        user_id=user_id,
                    )
                    stats["new_kg"] += 1
                else:
                    kg_id = resolution.kg_id

                # 保存别名（带待审核标记）
                self.store.save_alias(
                    alias_name=entity,
                    kg_id=kg_id,
                    pending_review=resolution.pending_review,
                    user_id=user_id,
                )
                stats["alias"] += 1

                # 保存切片与知识节点的映射
                self.store.save_chunk_map(
                    chunk_id=chunk.chunk_id,
                    kg_id=kg_id,
                    weight=1.0,
                    user_id=user_id,
                )
                stats["entities"] += 1

            # 处理同义词扩展
            for standard_name, synonyms in extraction.synonyms.items():
                # 获取标准名对应的 kg_id
                candidates = self.store.get_alias_candidates(standard_name)
                if candidates:
                    kg_id = candidates[0]["kg_id"]
                    for synonym in synonyms:
                        self.store.save_alias(
                            alias_name=synonym,
                            kg_id=kg_id,
                            pending_review=False,
                            user_id=user_id,
                        )

        return stats
