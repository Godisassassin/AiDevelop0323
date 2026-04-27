# -*- coding: utf-8 -*-
"""
Wiki 知识库 - AnswerSynthesizer 测试

Author: lhx
Date: 2026-04-27
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.service.wiki_knowledge.retrieval.answer_synthesizer import (
    AnswerSynthesizer,
    AnswerResult,
)
from app.service.wiki_knowledge.retrieval.action_filter import ScoredChunk


class TestAnswerSynthesizer:
    """AnswerSynthesizer 单元测试。"""

    @pytest.fixture
    def synthesizer(self):
        """创建 AnswerSynthesizer 实例。"""
        return AnswerSynthesizer()

    @pytest.fixture
    def sample_chunks(self):
        """创建示例切片。"""
        return [
            ScoredChunk(
                chunk_id="chunk-1",
                title_path="第一章 > 水杯清洗",
                content="水杯清洗的详细步骤：首先用清水冲洗，然后用中性洗涤剂清洗。",
                score=0.95,
                match_type="path_match",
            ),
            ScoredChunk(
                chunk_id="chunk-2",
                title_path="第一章 > 清洗剂选择",
                content="选择中性洗涤剂，避免使用强酸强碱。",
                score=0.85,
                match_type="entity_navigate",
            ),
            ScoredChunk(
                chunk_id="chunk-3",
                title_path="第二章 > 水杯保养",
                content="定期保养可以延长水杯使用寿命。",
                score=0.75,
                match_type="path_match",
            ),
        ]

    def test_answer_result_dataclass(self):
        """测试 AnswerResult 数据类。"""
        result = AnswerResult(
            answer="测试答案",
            sources=[{"chunk_id": "c1", "title_path": "标题", "score": 0.9}],
            generated_at="2026-04-27T10:00:00",
        )
        assert result.answer == "测试答案"
        assert len(result.sources) == 1
        assert result.sources[0]["chunk_id"] == "c1"

    def test_build_chunk_context(self, synthesizer, sample_chunks):
        """测试构建切片上下文。"""
        context = synthesizer._build_chunk_context(sample_chunks[:2])
        assert "第一章 > 水杯清洗" in context
        assert "第一章 > 清洗剂选择" in context
        assert "清水冲洗" in context

    def test_build_chunk_context_truncation(self, synthesizer):
        """测试长内容截断。"""
        long_chunk = ScoredChunk(
            chunk_id="long",
            title_path="长标题",
            content="x" * 1000,
            score=0.9,
            match_type="path_match",
        )
        context = synthesizer._build_chunk_context([long_chunk])
        assert "..." in context

    def test_build_prompt(self, synthesizer, sample_chunks):
        """测试构建 prompt。"""
        context = synthesizer._build_chunk_context(sample_chunks[:1])
        prompt = synthesizer._build_prompt("如何清洗水杯？", context)
        assert "如何清洗水杯？" in prompt
        assert "第一章 > 水杯清洗" in prompt

    def test_parse_response_success(self, synthesizer, sample_chunks):
        """测试解析正常 LLM 响应。"""
        import json

        llm_response = json.dumps({
            "answer": "清洗水杯的步骤：首先用清水冲洗。",
            "sources": [{"chunk_id": "chunk-1", "title_path": "第一章", "score": 0.95}],
        })
        result = synthesizer._parse_response(llm_response, sample_chunks[:1])
        assert "清洗水杯" in result.answer
        assert len(result.sources) == 1

    def test_parse_response_invalid_json(self, synthesizer, sample_chunks):
        """测试解析无效 JSON 响应。"""
        result = synthesizer._parse_response("这不是 JSON", sample_chunks[:1])
        assert result.sources is not None
        assert len(result.sources) == 1

    def test_fallback_answer(self, synthesizer, sample_chunks):
        """测试降级答案生成。"""
        result = synthesizer._fallback_answer("如何清洗？", sample_chunks[:1])
        assert "第一章 > 水杯清洗" in result.answer
        assert len(result.sources) == 1

    def test_fallback_answer_from_chunks(self, synthesizer, sample_chunks):
        """测试从切片生成降级答案。"""
        result = synthesizer._fallback_answer_from_chunks(sample_chunks[:2])
        assert "第一章 > 水杯清洗" in result.answer
        assert "第一章 > 清洗剂选择" in result.answer
        assert len(result.sources) == 2

    def test_fallback_answer_empty_chunks(self, synthesizer):
        """测试空切片列表的降级答案。"""
        result = synthesizer._fallback_answer("问题", [])
        assert result.answer == "抱歉，暂无相关信息。"
        assert result.sources == []

    @pytest.mark.asyncio
    async def test_synthesize_empty_chunks(self, synthesizer):
        """测试空切片列表生成答案。"""
        result = await synthesizer.synthesize("如何清洗？", [])
        assert result.answer == "抱歉，暂无相关信息。"
        assert result.sources == []

    @pytest.mark.asyncio
    async def test_synthesize_with_mock_llm(self, synthesizer, sample_chunks):
        """测试使用 Mock LLM 生成答案。"""
        import json

        mock_response = json.dumps({
            "answer": "清洗水杯的步骤：首先用清水冲洗，然后用中性洗涤剂清洗。",
            "sources": [
                {"chunk_id": "chunk-1", "title_path": "第一章 > 水杯清洗", "score": 0.95},
            ],
        })

        with patch.object(
            synthesizer,
            "_call_llm",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await synthesizer.synthesize("如何清洗水杯？", sample_chunks[:2])
            assert "清水冲洗" in result.answer or "清洗" in result.answer
            assert len(result.sources) == 2

    @pytest.mark.asyncio
    async def test_synthesize_llm_error(self, synthesizer, sample_chunks):
        """测试 LLM 调用失败时的降级处理。"""
        with patch.object(
            synthesizer,
            "_call_llm",
            new_callable=AsyncMock,
            side_effect=Exception("LLM 调用失败"),
        ):
            result = await synthesizer.synthesize("如何清洗？", sample_chunks[:1])
            assert "第一章 > 水杯清洗" in result.answer
            assert len(result.sources) == 1