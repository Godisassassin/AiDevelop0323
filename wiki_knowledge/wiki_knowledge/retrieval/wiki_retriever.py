# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 检索入口

串联 QueryParser → MultiMatchRetriever → ActionFilter → AnswerSynthesizer。

Author: lhx
Date: 2026-04-27
"""

from datetime import datetime
from typing import Optional

from app.service.wiki_knowledge.retrieval.query_parser import (
    QueryParser,
    ParsedQuery,
)
from app.service.wiki_knowledge.retrieval.multi_matcher import (
    MultiMatchRetriever,
    RetrievalCandidate,
)
from app.service.wiki_knowledge.retrieval.action_filter import (
    ActionFilter,
    ScoredChunk,
)
from app.service.wiki_knowledge.retrieval.answer_synthesizer import (
    AnswerSynthesizer,
    AnswerResult,
)


class WikiKnowledgeRetriever:
    """Wiki 知识库检索入口。

    串联完整的检索流程：
    1. QueryParser：解析用户查询
    2. MultiMatchRetriever：多路精准匹配
    3. ActionFilter：动作过滤与排序
    4. AnswerSynthesizer：答案生成

    Methods:
        retrieve: 执行完整检索流程
    """

    def __init__(self):
        """初始化检索流程各组件。"""
        self.query_parser = QueryParser()
        self.multi_matcher = MultiMatchRetriever()
        self.action_filter = ActionFilter()
        self.answer_synthesizer = AnswerSynthesizer()

    async def retrieve(
        self,
        query: str,
        knowledge_ids: Optional[list[str]] = None,
        limit: int = 10,
        top_k: int = 3,
    ) -> AnswerResult:
        """执行完整检索流程。

        Args:
            query: 用户查询
            knowledge_ids: 知识库ID列表（可选）
            limit: 返回切片数量限制
            top_k: 用于生成答案的切片数量

        Returns:
            AnswerResult：包含答案和来源信息
        """
        # Step 1: 解析用户查询
        parsed: ParsedQuery = await self.query_parser.parse(query)

        # Step 2: 多路精准匹配
        candidates: list[RetrievalCandidate] = await self.multi_matcher.retrieve(
            target=parsed.target,
            action=parsed.action,
            knowledge_ids=knowledge_ids,
            limit=limit,
        )

        # Step 3: 动作过滤与排序
        scored_chunks: list[ScoredChunk] = self.action_filter.filter_and_rank(
            candidates=candidates,
            action=parsed.action,
            limit=limit,
        )

        # Step 4: 答案生成
        result: AnswerResult = await self.answer_synthesizer.synthesize(
            query=query,
            chunks=scored_chunks,
            top_k=top_k,
        )

        return result