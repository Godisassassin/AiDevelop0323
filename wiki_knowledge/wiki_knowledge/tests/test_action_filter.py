# -*- coding: utf-8 -*-
"""
Wiki 知识库 - ActionFilter 测试

Author: lhx
Date: 2026-04-27
"""

import pytest

from app.service.wiki_knowledge.retrieval.action_filter import (
    ActionFilter,
    ScoredChunk,
)
from app.service.wiki_knowledge.retrieval.multi_matcher import RetrievalCandidate


class TestActionFilter:
    """ActionFilter 单元测试。"""

    @pytest.fixture
    def action_filter(self):
        """创建 ActionFilter 实例。"""
        return ActionFilter()

    @pytest.fixture
    def sample_candidates(self):
        """创建示例检索候选。"""
        return [
            RetrievalCandidate(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯清洗",
                content="水杯清洗的详细步骤，如何清洗水杯",
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
            RetrievalCandidate(
                chunk_id="chunk-3",
                title_path="第三章 > 水杯使用",
                content="水杯使用的注意事项",
                score=0.7,
                match_type="path_match",
            ),
        ]

    def test_filter_and_rank_empty(self, action_filter):
        """测试空候选列表。"""
        result = action_filter.filter_and_rank([], "如何")
        assert result == []

    def test_filter_and_rank_no_action(self, action_filter, sample_candidates):
        """测试无动作词时直接按分数排序。"""
        result = action_filter.filter_and_rank(sample_candidates, "")
        assert len(result) == 3
        assert result[0].chunk_id == "chunk-1"
        assert result[0].score == 0.9

    def test_filter_and_rank_with_action(self, action_filter, sample_candidates):
        """测试有动作词时的加权排序。"""
        result = action_filter.filter_and_rank(sample_candidates, "如何")
        assert len(result) == 3
        # chunk-1 的 content 包含"如何"，应该加权
        assert result[0].score > 0.9  # 0.9 + 0.1

    def test_filter_and_rank_action_in_title(self, action_filter, sample_candidates):
        """测试动作词出现在 title 中时的加权。"""
        # 添加一个 title 包含动作词的候选
        candidates = sample_candidates + [
            RetrievalCandidate(
                chunk_id="chunk-4",
                title_path="第四章 > 如何清洗",
                content="清洗方法的介绍",
                score=0.5,
                match_type="path_match",
            ),
        ]
        result = action_filter.filter_and_rank(candidates, "如何")
        # chunk-4 的 title 包含"如何"，应该有更高加权
        chunk4 = next(c for c in result if c.chunk_id == "chunk-4")
        assert chunk4.score == 0.5 + 0.3  # title 加权

    def test_filter_and_rank_limit(self, action_filter, sample_candidates):
        """测试结果数量限制。"""
        result = action_filter.filter_and_rank(sample_candidates, "", limit=2)
        assert len(result) == 2

    def test_calculate_action_score_no_action(self, action_filter, sample_candidates):
        """测试无动作词时分数为0。"""
        score = action_filter._calculate_action_score(sample_candidates[0], "")
        assert score == 0.0

    def test_calculate_action_score_in_content(self, action_filter, sample_candidates):
        """测试动作词出现在 content 中。"""
        score = action_filter._calculate_action_score(sample_candidates[0], "如何")
        assert score == 0.1  # ACTION_CONTENT_WEIGHT

    def test_calculate_action_score_in_title(self, action_filter):
        """测试动作词出现在 title 中。"""
        candidate = RetrievalCandidate(
            chunk_id="test",
            title_path="如何清洗",
            content="内容",
            score=0.5,
            match_type="path_match",
        )
        score = action_filter._calculate_action_score(candidate, "如何")
        assert score == 0.3  # ACTION_TITLE_WEIGHT

    def test_calculate_action_score_both(self, action_filter):
        """测试动作词同时出现在 title 和 content 中。"""
        candidate = RetrievalCandidate(
            chunk_id="test",
            title_path="如何清洗",
            content="如何清洗水杯",
            score=0.5,
            match_type="path_match",
        )
        score = action_filter._calculate_action_score(candidate, "如何")
        assert score == 0.3 + 0.1  # title + content

    def test_scored_chunk_dataclass(self):
        """测试 ScoredChunk 数据类。"""
        chunk = ScoredChunk(
            chunk_id="test-1",
            title_path="测试 > 标题",
            content="内容",
            score=0.95,
            match_type="path_match",
        )
        assert chunk.chunk_id == "test-1"
        assert chunk.title_path == "测试 > 标题"
        assert chunk.content == "内容"
        assert chunk.score == 0.95
        assert chunk.match_type == "path_match"