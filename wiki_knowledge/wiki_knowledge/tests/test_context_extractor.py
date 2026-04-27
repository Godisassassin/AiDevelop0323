# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 特征提取单元测试

测试 ContextAwareExtractor 的 JSON 响应解析和 prompt 构建逻辑。
使用 Mock LLM，不调用真实接口。

Author: lhx
Date: 2026-04-27

测试结果 (2026-04-27):
- ✅ test_extract_parses_json_response: PASSED
- ✅ test_extract_handles_json_decode_error: PASSED
- ✅ test_extract_handles_empty_response: PASSED
- ✅ test_build_context_prompt_contains_content: PASSED
- ✅ test_build_context_prompt_contains_parent_title: PASSED
- ✅ test_build_context_prompt_contains_sibling_titles: PASSED
- ✅ test_build_context_prompt_handles_missing_parent: PASSED
- ✅ test_build_context_prompt_handles_missing_siblings: PASSED
- ✅ test_build_context_prompt_truncates_long_content: PASSED
- ✅ test_extract_uses_call_llm: PASSED
- ✅ test_extract_returns_default_values: PASSED
"""

from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(ROOT_DIR))

import pytest  # noqa: E402
from unittest.mock import AsyncMock, patch  # noqa: E402

from app.service.wiki_knowledge.processor.context_extractor import (  # noqa: E402
    ContextAwareExtractor,
    ExtractionResult,
)


class MockChunkResult:
    """模拟的 ChunkResult 对象"""

    def __init__(self, content, parent_title=None, sibling_titles=None):
        self.content = content
        self.parent_title = parent_title
        self.sibling_titles = sibling_titles or []


class TestContextAwareExtractor:
    """测试 ContextAwareExtractor 特征提取器"""

    @pytest.fixture
    def extractor(self):
        """创建 ContextAwareExtractor 实例"""
        return ContextAwareExtractor()

    @pytest.fixture
    def sample_chunk(self):
        """创建示例切片"""
        return MockChunkResult(
            content="这是一个关于深度学习的文档。深度学习是机器学习的分支。",
            parent_title="机器学习",
            sibling_titles=["神经网络", "卷积神经网络"],
        )

    @pytest.mark.asyncio
    async def test_extract_parses_json_response(self, extractor, sample_chunk):
        """测试 extract() 正确解析 JSON 响应"""
        mock_response = """{
            "entities": ["深度学习", "机器学习"],
            "concepts": ["神经网络"],
            "synonyms": {
                "深度学习": ["深度学习技术", "Deep Learning"],
                "机器学习": ["ML", "机器学习算法"]
            }
        }"""

        with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await extractor.extract(sample_chunk)

        assert isinstance(result, ExtractionResult)
        assert "深度学习" in result.entities
        assert "机器学习" in result.entities
        assert "神经网络" in result.concepts
        assert "深度学习技术" in result.synonyms.get("深度学习", [])

    @pytest.mark.asyncio
    async def test_extract_handles_json_decode_error(self, extractor, sample_chunk):
        """测试 JSON 解析异常时返回空 ExtractionResult"""
        mock_response = "这不是有效的JSON格式"

        with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await extractor.extract(sample_chunk)

        assert isinstance(result, ExtractionResult)
        assert result.entities == []
        assert result.concepts == []
        assert result.synonyms == {}

    @pytest.mark.asyncio
    async def test_extract_handles_empty_response(self, extractor, sample_chunk):
        """测试空响应时返回空 ExtractionResult"""
        mock_response = "{}"

        with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await extractor.extract(sample_chunk)

        assert result.entities == []
        assert result.concepts == []
        assert result.synonyms == {}

    def test_build_context_prompt_contains_content(self, extractor, sample_chunk):
        """测试构建的 prompt 包含切片内容"""
        prompt = extractor._build_context_prompt(sample_chunk)

        assert sample_chunk.content in prompt

    def test_build_context_prompt_contains_parent_title(self, extractor, sample_chunk):
        """测试构建的 prompt 包含父级标题"""
        prompt = extractor._build_context_prompt(sample_chunk)

        assert sample_chunk.parent_title in prompt

    def test_build_context_prompt_contains_sibling_titles(self, extractor, sample_chunk):
        """测试构建的 prompt 包含同级标题"""
        prompt = extractor._build_context_prompt(sample_chunk)

        for sibling in sample_chunk.sibling_titles:
            assert sibling in prompt

    def test_build_context_prompt_handles_missing_parent(self, extractor):
        """测试父级标题为空时的处理"""
        chunk = MockChunkResult(content="内容", parent_title=None, sibling_titles=[])
        prompt = extractor._build_context_prompt(chunk)

        assert "无" in prompt

    def test_build_context_prompt_handles_missing_siblings(self, extractor):
        """测试同级标题为空时的处理"""
        chunk = MockChunkResult(content="内容", parent_title="父标题", sibling_titles=[])
        prompt = extractor._build_context_prompt(chunk)

        assert "无" in prompt

    def test_build_context_prompt_truncates_long_content(self, extractor):
        """测试长内容被截断"""
        long_content = "A" * 3000
        chunk = MockChunkResult(content=long_content)
        prompt = extractor._build_context_prompt(chunk)

        # 内容应被截断到2000字符
        assert len(chunk.content) == 3000
        # prompt 中的内容应该不超过2000字符
        # 提取 prompt 中的内容部分
        content_start = prompt.find("当前切片：\n") + len("当前切片：\n")
        content_end = prompt.find("\n\n父级标题")
        actual_content = prompt[content_start:content_end]

        assert len(actual_content) <= 2000

    @pytest.mark.asyncio
    async def test_extract_uses_call_llm(self, extractor, sample_chunk):
        """测试 extract 调用 _call_llm"""
        with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "{}"
            await extractor.extract(sample_chunk)

            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_returns_default_values(self, extractor, sample_chunk):
        """测试 extract 返回默认值"""
        mock_response = '{"entities": [], "concepts": [], "synonyms": {}}'

        with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await extractor.extract(sample_chunk)

        assert result.entities == []
        assert result.concepts == []
        assert result.synonyms == {}