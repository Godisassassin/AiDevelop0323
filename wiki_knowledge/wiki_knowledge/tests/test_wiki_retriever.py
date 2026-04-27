# -*- coding: utf-8 -*-
"""
Wiki 知识库 - WikiKnowledgeRetriever 测试

Author: lhx
Date: 2026-04-27
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.service.wiki_knowledge.retrieval.wiki_retriever import WikiKnowledgeRetriever
from app.service.wiki_knowledge.retrieval.query_parser import ParsedQuery
from app.service.wiki_knowledge.retrieval.multi_matcher import RetrievalCandidate
from app.service.wiki_knowledge.retrieval.action_filter import ScoredChunk
from app.service.wiki_knowledge.retrieval.answer_synthesizer import AnswerResult


class TestWikiKnowledgeRetriever:
    """WikiKnowledgeRetriever 单元测试。"""

    @pytest.fixture
    def retriever(self):
        """创建 WikiKnowledgeRetriever 实例。"""
        return WikiKnowledgeRetriever()

    @pytest.fixture
    def sample_candidates(self):
        """创建示例检索候选。"""
        return [
            RetrievalCandidate(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯清洗",
                content="水杯清洗的详细步骤",
                score=0.9,
                match_type="path_match",
            ),
            RetrievalCandidate(
                chunk_id="chunk-2",
                title_path="第二章 > 设备维护",
                content="设备维护的基本方法",
                score=0.8,
                match_type="entity_navigate",
            ),
        ]

    @pytest.fixture
    def sample_scored_chunks(self):
        """创建示例评分切片。"""
        return [
            ScoredChunk(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯清洗",
                content="水杯清洗的详细步骤",
                score=0.95,
                match_type="path_match",
            ),
            ScoredChunk(
                chunk_id="chunk-2",
                title_path="第二章 > 设备维护",
                content="设备维护的基本方法",
                score=0.85,
                match_type="entity_navigate",
            ),
        ]

    @pytest.mark.asyncio
    async def test_retrieve_full_flow(self, retriever, sample_candidates, sample_scored_chunks):
        """测试完整检索流程。"""
        with patch.object(
            retriever.query_parser,
            "parse",
            new_callable=AsyncMock,
            return_value=ParsedQuery(
                target="水杯",
                action="如何",
                original_query="如何清洗水杯？",
            ),
        ), patch.object(
            retriever.multi_matcher,
            "retrieve",
            new_callable=AsyncMock,
            return_value=sample_candidates,
        ), patch.object(
            retriever.action_filter,
            "filter_and_rank",
            return_value=sample_scored_chunks,
        ), patch.object(
            retriever.answer_synthesizer,
            "synthesize",
            new_callable=AsyncMock,
            return_value=AnswerResult(
                answer="清洗水杯的步骤：首先用清水冲洗。",
                sources=[{"chunk_id": "chunk-1", "title_path": "第一章", "score": 0.95}],
                generated_at="2026-04-27T10:00:00",
            ),
        ):
            result = await retriever.retrieve("如何清洗水杯？")

            assert result.answer == "清洗水杯的步骤：首先用清水冲洗。"
            assert len(result.sources) == 1

    @pytest.mark.asyncio
    async def test_retrieve_with_knowledge_ids(self, retriever, sample_candidates, sample_scored_chunks):
        """测试带知识库ID的检索。"""
        with patch.object(
            retriever.query_parser,
            "parse",
            new_callable=AsyncMock,
            return_value=ParsedQuery(
                target="水杯",
                action="如何",
                original_query="如何清洗水杯？",
            ),
        ), patch.object(
            retriever.multi_matcher,
            "retrieve",
            new_callable=AsyncMock,
            return_value=sample_candidates,
        ), patch.object(
            retriever.action_filter,
            "filter_and_rank",
            return_value=sample_scored_chunks,
        ), patch.object(
            retriever.answer_synthesizer,
            "synthesize",
            new_callable=AsyncMock,
            return_value=AnswerResult(
                answer="清洗水杯",
                sources=[],
                generated_at="2026-04-27T10:00:00",
            ),
        ):
            result = await retriever.retrieve(
                "如何清洗水杯？",
                knowledge_ids=["kg-1", "kg-2"],
                limit=5,
                top_k=3,
            )

            # 验证 multi_matcher 被调用时传入了 knowledge_ids
            retriever.multi_matcher.retrieve.assert_called_once()
            call_args = retriever.multi_matcher.retrieve.call_args
            assert call_args.kwargs.get("knowledge_ids") == ["kg-1", "kg-2"]
            assert call_args.kwargs.get("limit") == 5

    @pytest.mark.asyncio
    async def test_retrieve_empty_result(self, retriever):
        """测试空结果检索。"""
        with patch.object(
            retriever.query_parser,
            "parse",
            new_callable=AsyncMock,
            return_value=ParsedQuery(
                target="不存在的实体",
                action="如何",
                original_query="如何xxx？",
            ),
        ), patch.object(
            retriever.multi_matcher,
            "retrieve",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            retriever.action_filter,
            "filter_and_rank",
            return_value=[],
        ), patch.object(
            retriever.answer_synthesizer,
            "synthesize",
            new_callable=AsyncMock,
            return_value=AnswerResult(
                answer="抱歉，暂无相关信息。",
                sources=[],
                generated_at="2026-04-27T10:00:00",
            ),
        ):
            result = await retriever.retrieve("如何xxx？")

            assert result.answer == "抱歉，暂无相关信息。"
            assert result.sources == []

    @pytest.mark.asyncio
    async def test_retrieve_passes_top_k(self, retriever, sample_candidates, sample_scored_chunks):
        """测试 top_k 参数传递。"""
        with patch.object(
            retriever.query_parser,
            "parse",
            new_callable=AsyncMock,
            return_value=ParsedQuery(
                target="水杯",
                action="如何",
                original_query="如何清洗水杯？",
            ),
        ), patch.object(
            retriever.multi_matcher,
            "retrieve",
            new_callable=AsyncMock,
            return_value=sample_candidates,
        ), patch.object(
            retriever.action_filter,
            "filter_and_rank",
            return_value=sample_scored_chunks,
        ), patch.object(
            retriever.answer_synthesizer,
            "synthesize",
            new_callable=AsyncMock,
            return_value=AnswerResult(
                answer="答案",
                sources=[],
                generated_at="2026-04-27T10:00:00",
            ),
        ):
            await retriever.retrieve("如何清洗水杯？", top_k=5)

            # 验证 answer_synthesizer 被调用时传入了正确的 top_k
            retriever.answer_synthesizer.synthesize.assert_called_once()
            call_args = retriever.answer_synthesizer.synthesize.call_args
            assert call_args.kwargs.get("top_k") == 5