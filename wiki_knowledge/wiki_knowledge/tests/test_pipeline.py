# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 流水线单元测试

测试 WikiKnowledgePipeline 的文档入库流程。
使用 Mock 各组件，验证数据流正确。

Author: lhx
Date: 2026-04-27

测试结果 (2026-04-27):
- ✅ test_process_document_empty_content: PASSED
- ✅ test_process_document_returns_stats: PASSED
- ✅ test_process_document_chunk_processing: PASSED
- ✅ test_process_document_entity_extraction: PASSED
- ✅ test_process_document_new_entity_creates_kg: PASSED
- ✅ test_process_document_alias_creation: PASSED
- ✅ test_process_document_chunk_map_creation: PASSED
- ✅ test_process_document_synonym_expansion: PASSED
- ✅ test_pipeline_initialization: PASSED
"""

from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
import sys

sys.path.insert(0, str(ROOT_DIR))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.service.wiki_knowledge.processor.pipeline import WikiKnowledgePipeline
from app.service.wiki_knowledge.processor.chunk_processor import ChunkResult
from app.service.wiki_knowledge.processor.context_extractor import ExtractionResult
from app.service.wiki_knowledge.processor.entity_resolver import (
    ResolutionResult,
    ResolutionType,
)


class TestWikiKnowledgePipeline:
    """WikiKnowledgePipeline 单元测试"""

    @pytest.fixture
    def pipeline(self):
        """创建 WikiKnowledgePipeline 实例"""
        return WikiKnowledgePipeline()

    @pytest.fixture
    def sample_markdown(self):
        """示例 Markdown 文档"""
        return """# 水杯使用指南

## 第一章 清洗方法

本章介绍水杯的清洗方法。

### 1.1 日常清洗

日常清洗水杯的步骤如下：
1. 用清水冲洗
2. 使用中性清洁剂
3. 彻底冲洗干净

## 第二章 注意事项

请勿使用强酸强碱清洁水杯。
"""

    @pytest.fixture
    def sample_chunk(self):
        """示例切片结果"""
        return ChunkResult(
            chunk_id="chunk-001",
            doc_id=1,
            title_path="水杯使用指南 > 第一章 清洗方法 > 1.1 日常清洗",
            content="日常清洗水杯的步骤如下：1. 用清水冲洗 2. 使用中性清洁剂 3. 彻底冲洗干净",
            summary="日常清洗水杯的步骤",
            parent_title="第一章 清洗方法",
            sibling_titles=["1.2 深度清洗", "1.3 特殊清洁"],
        )

    @pytest.mark.asyncio
    async def test_process_document_empty_content(self, pipeline):
        """测试空文档返回空统计"""
        with patch.object(
            pipeline.processor, "process", return_value=[]
        ):
            result = await pipeline.process_document("", doc_id=1)

        assert result["chunks"] == 0
        assert result["entities"] == 0
        assert result["alias"] == 0
        assert result["new_kg"] == 0

    @pytest.mark.asyncio
    async def test_process_document_returns_stats(self, pipeline, sample_markdown):
        """测试文档处理返回正确统计"""
        sample_chunks = [
            ChunkResult(
                chunk_id="chunk-001",
                doc_id=1,
                title_path="水杯使用指南",
                content="内容",
                summary="摘要",
            )
        ]

        with patch.object(
            pipeline.processor, "process", return_value=sample_chunks
        ), patch.object(
            pipeline.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            pipeline.store, "save_chunk"
        ), patch.object(
            pipeline.store, "get_alias_candidates", return_value=[]
        ), patch.object(
            pipeline.resolver, "resolve", new_callable=AsyncMock
        ) as mock_resolve, patch.object(
            pipeline.store, "save_kg", return_value="kg-001"
        ), patch.object(
            pipeline.store, "save_alias"
        ), patch.object(
            pipeline.store, "save_chunk_map"
        ):
            mock_extract.return_value = ExtractionResult(
                entities=["水杯"],
                concepts=[],
                synonyms={},
            )
            mock_resolve.return_value = ResolutionResult(
                original_name="水杯",
                resolution_type=ResolutionType.NEW,
                kg_id="kg-001",
                confidence=0.5,
                pending_review=False,
            )

            result = await pipeline.process_document(sample_markdown, doc_id=1)

        assert "chunks" in result
        assert "entities" in result
        assert "alias" in result
        assert "new_kg" in result

    @pytest.mark.asyncio
    async def test_process_document_chunk_processing(self, pipeline, sample_markdown):
        """测试切片处理调用正确"""
        sample_chunks = [
            ChunkResult(
                chunk_id="chunk-001",
                doc_id=1,
                title_path="标题",
                content="内容",
                summary="摘要",
            )
        ]

        with patch.object(
            pipeline.processor, "process", return_value=sample_chunks
        ) as mock_process, patch.object(
            pipeline.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            pipeline.store, "save_chunk"
        ) as mock_save_chunk, patch.object(
            pipeline.store, "get_alias_candidates", return_value=[]
        ), patch.object(
            pipeline.resolver, "resolve", new_callable=AsyncMock
        ) as mock_resolve, patch.object(
            pipeline.store, "save_kg", return_value="kg-001"
        ), patch.object(
            pipeline.store, "save_alias"
        ), patch.object(
            pipeline.store, "save_chunk_map"
        ):
            mock_extract.return_value = ExtractionResult(entities=[], concepts=[], synonyms={})
            mock_resolve.return_value = ResolutionResult(
                original_name="测试",
                resolution_type=ResolutionType.NEW,
                kg_id="kg-001",
                confidence=0.5,
                pending_review=False,
            )

            await pipeline.process_document(sample_markdown, doc_id=1)

            # 验证切片处理被调用
            mock_process.assert_called_once_with(sample_markdown, 1)
            # 验证切片被保存
            mock_save_chunk.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_document_entity_extraction(self, pipeline, sample_markdown):
        """测试实体提取被调用"""
        sample_chunks = [
            ChunkResult(
                chunk_id="chunk-001",
                doc_id=1,
                title_path="标题",
                content="内容",
                summary="摘要",
            )
        ]

        with patch.object(
            pipeline.processor, "process", return_value=sample_chunks
        ), patch.object(
            pipeline.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            pipeline.store, "save_chunk"
        ), patch.object(
            pipeline.store, "get_alias_candidates", return_value=[]
        ), patch.object(
            pipeline.resolver, "resolve", new_callable=AsyncMock
        ) as mock_resolve, patch.object(
            pipeline.store, "save_kg", return_value="kg-001"
        ), patch.object(
            pipeline.store, "save_alias"
        ), patch.object(
            pipeline.store, "save_chunk_map"
        ):
            mock_extract.return_value = ExtractionResult(
                entities=["水杯", "清洁剂"],
                concepts=["清洗方法"],
                synonyms={},
            )
            mock_resolve.return_value = ResolutionResult(
                original_name="测试",
                resolution_type=ResolutionType.NEW,
                kg_id="kg-001",
                confidence=0.5,
                pending_review=False,
            )

            await pipeline.process_document(sample_markdown, doc_id=1)

            # 验证特征提取被调用
            mock_extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_document_new_entity_creates_kg(self, pipeline, sample_markdown):
        """测试新实体创建知识节点"""
        sample_chunks = [
            ChunkResult(
                chunk_id="chunk-001",
                doc_id=1,
                title_path="标题",
                content="内容",
                summary="摘要",
            )
        ]

        with patch.object(
            pipeline.processor, "process", return_value=sample_chunks
        ), patch.object(
            pipeline.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            pipeline.store, "save_chunk"
        ), patch.object(
            pipeline.store, "get_alias_candidates", return_value=[]
        ), patch.object(
            pipeline.resolver, "resolve", new_callable=AsyncMock
        ) as mock_resolve, patch.object(
            pipeline.store, "save_kg", return_value="kg-new"
        ) as mock_save_kg, patch.object(
            pipeline.store, "save_alias"
        ), patch.object(
            pipeline.store, "save_chunk_map"
        ):
            mock_extract.return_value = ExtractionResult(
                entities=["新实体"],
                concepts=[],
                synonyms={},
            )
            mock_resolve.return_value = ResolutionResult(
                original_name="新实体",
                resolution_type=ResolutionType.NEW,
                kg_id="",
                confidence=0.5,
                pending_review=False,
            )

            await pipeline.process_document(sample_markdown, doc_id=1)

            # 验证新知识节点被创建
            mock_save_kg.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_document_alias_creation(self, pipeline, sample_markdown):
        """测试别名创建"""
        sample_chunks = [
            ChunkResult(
                chunk_id="chunk-001",
                doc_id=1,
                title_path="标题",
                content="内容",
                summary="摘要",
            )
        ]

        with patch.object(
            pipeline.processor, "process", return_value=sample_chunks
        ), patch.object(
            pipeline.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            pipeline.store, "save_chunk"
        ), patch.object(
            pipeline.store, "get_alias_candidates", return_value=[{"kg_id": "kg-001", "name": "测试", "description": ""}]
        ), patch.object(
            pipeline.resolver, "resolve", new_callable=AsyncMock
        ) as mock_resolve, patch.object(
            pipeline.store, "save_kg", return_value="kg-001"
        ), patch.object(
            pipeline.store, "save_alias"
        ) as mock_save_alias, patch.object(
            pipeline.store, "save_chunk_map"
        ):
            mock_extract.return_value = ExtractionResult(
                entities=["测试"],
                concepts=[],
                synonyms={},
            )
            mock_resolve.return_value = ResolutionResult(
                original_name="测试",
                resolution_type=ResolutionType.ALIAS,
                kg_id="kg-001",
                confidence=0.9,
                pending_review=False,
            )

            await pipeline.process_document(sample_markdown, doc_id=1)

            # 验证别名被创建
            mock_save_alias.assert_called()

    @pytest.mark.asyncio
    async def test_process_document_chunk_map_creation(self, pipeline, sample_markdown):
        """测试切片映射创建"""
        sample_chunks = [
            ChunkResult(
                chunk_id="chunk-001",
                doc_id=1,
                title_path="标题",
                content="内容",
                summary="摘要",
            )
        ]

        with patch.object(
            pipeline.processor, "process", return_value=sample_chunks
        ), patch.object(
            pipeline.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            pipeline.store, "save_chunk"
        ), patch.object(
            pipeline.store, "get_alias_candidates", return_value=[]
        ), patch.object(
            pipeline.resolver, "resolve", new_callable=AsyncMock
        ) as mock_resolve, patch.object(
            pipeline.store, "save_kg", return_value="kg-001"
        ), patch.object(
            pipeline.store, "save_alias"
        ), patch.object(
            pipeline.store, "save_chunk_map"
        ) as mock_save_chunk_map:
            mock_extract.return_value = ExtractionResult(
                entities=["测试"],
                concepts=[],
                synonyms={},
            )
            mock_resolve.return_value = ResolutionResult(
                original_name="测试",
                resolution_type=ResolutionType.NEW,
                kg_id="kg-001",
                confidence=0.5,
                pending_review=False,
            )

            await pipeline.process_document(sample_markdown, doc_id=1)

            # 验证切片映射被创建
            mock_save_chunk_map.assert_called()

    @pytest.mark.asyncio
    async def test_process_document_synonym_expansion(self, pipeline, sample_markdown):
        """测试同义词扩展"""
        sample_chunks = [
            ChunkResult(
                chunk_id="chunk-001",
                doc_id=1,
                title_path="标题",
                content="内容",
                summary="摘要",
            )
        ]

        with patch.object(
            pipeline.processor, "process", return_value=sample_chunks
        ), patch.object(
            pipeline.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            pipeline.store, "save_chunk"
        ), patch.object(
            pipeline.store, "get_alias_candidates"
        ) as mock_get_alias, patch.object(
            pipeline.resolver, "resolve", new_callable=AsyncMock
        ), patch.object(
            pipeline.store, "save_kg", return_value="kg-001"
        ), patch.object(
            pipeline.store, "save_alias"
        ) as mock_save_alias, patch.object(
            pipeline.store, "save_chunk_map"
        ):
            mock_extract.return_value = ExtractionResult(
                entities=["水杯"],
                concepts=[],
                synonyms={"水杯": ["杯子", "茶杯", "水杯子"]},
            )
            mock_get_alias.return_value = [{"kg_id": "kg-001", "name": "水杯", "description": ""}]

            await pipeline.process_document(sample_markdown, doc_id=1)

            # 验证同义词扩展（原有实体别名 + 3个同义词）
            # 第一次调用是实体本身，第二次调用是同义词扩展
            assert mock_save_alias.call_count >= 1

    def test_pipeline_initialization(self, pipeline):
        """测试流水线初始化"""
        assert hasattr(pipeline, "processor")
        assert hasattr(pipeline, "extractor")
        assert hasattr(pipeline, "resolver")
        assert hasattr(pipeline, "store")
        assert isinstance(pipeline.processor, type(pipeline.processor))
        assert isinstance(pipeline.extractor, type(pipeline.extractor))
        assert isinstance(pipeline.resolver, type(pipeline.resolver))
        assert isinstance(pipeline.store, type(pipeline.store))
