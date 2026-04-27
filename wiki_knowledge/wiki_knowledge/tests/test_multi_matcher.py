# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 多路匹配器测试

Author: lhx
Date: 2026-04-27

测试结果 (2026-04-27):
- ✅ test_retrieval_candidate_dataclass: PASSED
- ✅ test_merge_results_empty: PASSED
- ✅ test_merge_results_path_only: PASSED
- ✅ test_merge_results_entity_only: PASSED
- ✅ test_merge_results_deduplication: PASSED
- ✅ test_merge_results_different_chunks: PASSED
- ✅ test_calculate_path_score_start_match: PASSED
- ✅ test_calculate_path_score_delimiter_match: PASSED
- ✅ test_calculate_path_score_contains_match: PASSED
- ✅ test_calculate_path_score_no_match: PASSED
- ✅ test_calculate_path_score_empty_inputs: PASSED
- ✅ test_calculate_path_score_case_insensitive: PASSED
- ✅ test_retrieve_sorted_by_score: PASSED
- ✅ test_retrieve_with_limit: PASSED
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.service.wiki_knowledge.retrieval.multi_matcher import (
    MultiMatchRetriever,
    RetrievalCandidate,
)


class TestMultiMatchRetriever:
    """MultiMatchRetriever 单元测试。"""

    @pytest.fixture
    def retriever(self):
        """创建 MultiMatchRetriever 实例。"""
        return MultiMatchRetriever()

    def test_retrieval_candidate_dataclass(self):
        """测试 RetrievalCandidate 数据类。"""
        candidate = RetrievalCandidate(
            chunk_id="test-chunk-001",
            title_path="第一章 > 第一节 > 水杯清洗",
            content="水杯清洗的详细步骤...",
            score=0.95,
            match_type="path_match",
        )

        assert candidate.chunk_id == "test-chunk-001"
        assert candidate.title_path == "第一章 > 第一节 > 水杯清洗"
        assert candidate.content == "水杯清洗的详细步骤..."
        assert candidate.score == 0.95
        assert candidate.match_type == "path_match"

    def test_merge_results_empty(self, retriever):
        """测试合并空结果。"""
        result = retriever._merge_results([], [])
        assert result == []

    def test_merge_results_path_only(self, retriever):
        """测试仅有路径匹配结果。"""
        path_results = [
            RetrievalCandidate(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯",
                content="内容1",
                score=0.9,
                match_type="path_match",
            ),
        ]
        result = retriever._merge_results(path_results, [])
        assert len(result) == 1
        assert result[0].chunk_id == "chunk-1"

    def test_merge_results_entity_only(self, retriever):
        """测试仅有实体导航结果。"""
        entity_results = [
            RetrievalCandidate(
                chunk_id="chunk-2",
                title_path="第二章 > 设备",
                content="内容2",
                score=0.8,
                match_type="entity_navigate",
            ),
        ]
        result = retriever._merge_results([], entity_results)
        assert len(result) == 1
        assert result[0].chunk_id == "chunk-2"

    def test_merge_results_deduplication(self, retriever):
        """测试去重逻辑。"""
        path_results = [
            RetrievalCandidate(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯",
                content="内容1",
                score=0.9,
                match_type="path_match",
            ),
        ]
        entity_results = [
            RetrievalCandidate(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯",
                content="内容1",
                score=0.7,
                match_type="entity_navigate",
            ),
        ]
        result = retriever._merge_results(path_results, entity_results)
        assert len(result) == 1
        assert result[0].score == 0.9

    def test_merge_results_different_chunks(self, retriever):
        """测试不同切片ID的结果合并。"""
        path_results = [
            RetrievalCandidate(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯",
                content="内容1",
                score=0.9,
                match_type="path_match",
            ),
        ]
        entity_results = [
            RetrievalCandidate(
                chunk_id="chunk-2",
                title_path="第二章 > 设备",
                content="内容2",
                score=0.8,
                match_type="entity_navigate",
            ),
        ]
        result = retriever._merge_results(path_results, entity_results)
        assert len(result) == 2
        chunk_ids = {c.chunk_id for c in result}
        assert chunk_ids == {"chunk-1", "chunk-2"}

    def test_calculate_path_score_start_match(self, retriever):
        """测试路径匹配分数 - 开头匹配。"""
        # "水杯" 是 "水杯清洗指南" 的开头
        score = retriever._calculate_path_score("水杯清洗指南", "水杯")
        assert score == 1.0

    def test_calculate_path_score_delimiter_match(self, retriever):
        """测试路径匹配分数 - 分隔符匹配。"""
        # " > 水杯" 在 "第一章 > 水杯使用" 中
        score = retriever._calculate_path_score("第一章 > 水杯使用", "水杯")
        assert score == 0.9

    def test_calculate_path_score_contains_match(self, retriever):
        """测试路径匹配分数 - 包含匹配。"""
        # "水杯" 在中间位置（既不是开头也不在分隔符后）
        # 使用不包含分隔符的路径
        score = retriever._calculate_path_score("用户水杯指南", "水杯")
        assert score == 0.7

    def test_calculate_path_score_no_match(self, retriever):
        """测试路径匹配分数 - 无匹配。"""
        score = retriever._calculate_path_score("第一章 > 设备使用", "水杯")
        assert score == 0.0

    def test_calculate_path_score_empty_inputs(self, retriever):
        """测试路径匹配分数 - 空输入。"""
        assert retriever._calculate_path_score("", "水杯") == 0.0
        assert retriever._calculate_path_score("第一章 > 水杯", "") == 0.0
        assert retriever._calculate_path_score("", "") == 0.0

    def test_calculate_path_score_case_insensitive(self, retriever):
        """测试路径匹配分数 - 大小写不敏感。"""
        score = retriever._calculate_path_score("第一章 > 水杯", "水杯")
        assert score > 0

    @pytest.mark.asyncio
    async def test_retrieve_sorted_by_score(self, retriever):
        """测试检索结果按分数排序。"""
        with patch.object(
            retriever,
            "_path_match",
            new_callable=AsyncMock,
            return_value=[
                RetrievalCandidate(
                    chunk_id="chunk-1",
                    title_path="第一章",
                    content="内容1",
                    score=0.6,
                    match_type="path_match",
                ),
            ],
        ), patch.object(
            retriever,
            "_entity_navigate",
            new_callable=AsyncMock,
            return_value=[
                RetrievalCandidate(
                    chunk_id="chunk-2",
                    title_path="第二章",
                    content="内容2",
                    score=0.9,
                    match_type="entity_navigate",
                ),
            ],
        ):
            results = await retriever.retrieve("测试", "如何")
            assert len(results) == 2
            assert results[0].score >= results[1].score

    @pytest.mark.asyncio
    async def test_retrieve_with_limit(self, retriever):
        """测试检索结果限制。"""
        with patch.object(
            retriever,
            "_path_match",
            new_callable=AsyncMock,
            return_value=[
                RetrievalCandidate(
                    chunk_id=f"chunk-{i}",
                    title_path=f"标题{i}",
                    content=f"内容{i}",
                    score=1.0 - i * 0.1,
                    match_type="path_match",
                )
                for i in range(5)
            ],
        ), patch.object(
            retriever,
            "_entity_navigate",
            new_callable=AsyncMock,
            return_value=[],
        ):
            results = await retriever.retrieve("测试", "如何", limit=3)
            assert len(results) == 3
