# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 切片处理单元测试

测试 WikiChunkProcessor 的 Markdown 解析和切片逻辑。

Author: lhx
Date: 2026-04-27

测试结果 (2026-04-27):
- ✅ test_process_with_h1_h4_headers: PASSED
- ✅ test_chunk_contains_required_fields: PASSED
- ✅ test_parent_title_extraction: PASSED
- ✅ test_sibling_titles_extraction: PASSED
- ✅ test_empty_document: PASSED
- ✅ test_no_headers: PASSED
- ✅ test_summary_generation: PASSED
- ✅ test_chunk_id_uniqueness: PASSED
- ✅ test_hierarchical_title_path: PASSED
"""

from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(ROOT_DIR))

import pytest  # noqa: E402

from app.service.wiki_knowledge.processor.chunk_processor import (  # noqa: E402
    WikiChunkProcessor,
    ChunkResult,
)


class TestWikiChunkProcessor:
    """测试 WikiChunkProcessor 切片处理器"""

    @pytest.fixture
    def processor(self):
        """创建 WikiChunkProcessor 实例"""
        return WikiChunkProcessor()

    def test_process_with_h1_h4_headers(self, processor):
        """测试按 H1-H4 标题正确切分"""
        markdown = """# 第一章

这是第一章的内容。

## 第一节

这是第一节的内容。

### 第一小节

这是第一小节的内容。

## 第二节

这是第二节的内容。

# 第二章

这是第二章的内容。
"""
        chunks = processor.process(markdown, doc_id=123)

        assert len(chunks) == 5
        # 验证第一个切片
        assert chunks[0].doc_id == 123
        assert chunks[0].title_path == "第一章"
        assert "这是第一章的内容" in chunks[0].content
        assert chunks[0].parent_title is None

    def test_chunk_contains_required_fields(self, processor):
        """测试每个切片包含必需字段"""
        markdown = """# 标题

内容
"""
        chunks = processor.process(markdown, doc_id=1)

        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk.chunk_id is not None
        assert chunk.doc_id == 1
        assert chunk.title_path == "标题"
        assert chunk.content == "内容"
        assert chunk.summary is not None

    def test_parent_title_extraction(self, processor):
        """测试父级标题正确提取"""
        markdown = """# 主标题

## 子标题

### 孙标题

内容
"""
        chunks = processor.process(markdown, doc_id=1)

        # 找到内容所在的切片
        content_chunk = None
        for chunk in chunks:
            if chunk.content == "内容":
                content_chunk = chunk
                break

        assert content_chunk is not None
        # parent_title = 父级标题（H2 "子标题"），因为 H3 "孙标题" 的父级是 H2
        assert content_chunk.parent_title == "子标题"

    def test_sibling_titles_extraction(self, processor):
        """测试同级标题列表正确提取"""
        markdown = """# 主标题

## 同级A

内容A

## 同级B

内容B

## 同级C

内容C
"""
        chunks = processor.process(markdown, doc_id=1)

        # 找到内容B所在的切片
        content_b_chunk = None
        for chunk in chunks:
            if chunk.content == "内容B":
                content_b_chunk = chunk
                break

        assert content_b_chunk is not None
        assert "同级A" in content_b_chunk.sibling_titles
        assert "同级C" in content_b_chunk.sibling_titles
        assert "同级B" not in content_b_chunk.sibling_titles

    def test_empty_document(self, processor):
        """测试空文档返回空列表"""
        chunks = processor.process("", doc_id=1)
        assert chunks == []

        chunks = processor.process("   ", doc_id=1)
        assert chunks == []

    def test_no_headers(self, processor):
        """测试无标题文档整个作为切片"""
        markdown = "这是没有任何标题的文档内容。"
        chunks = processor.process(markdown, doc_id=1)

        assert len(chunks) == 1
        assert chunks[0].title_path == ""
        assert chunks[0].content == "这是没有任何标题的文档内容。"

    def test_summary_generation(self, processor):
        """测试摘要生成"""
        long_content = "A" * 200
        markdown = f"""# 标题

{long_content}
"""
        chunks = processor.process(markdown, doc_id=1)

        assert len(chunks) == 1
        assert len(chunks[0].summary) <= 103  # 100 + "..."
        assert chunks[0].summary.endswith("...")

    def test_chunk_id_uniqueness(self, processor):
        """测试切片ID唯一性"""
        markdown = """# 标题1

内容1

# 标题2

内容2
"""
        chunks = processor.process(markdown, doc_id=1)

        chunk_ids = [chunk.chunk_id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))

    def test_hierarchical_title_path(self, processor):
        """测试层级标题路径构建"""
        markdown = """# 第一章

## 第一节

### 第一小节

内容
"""
        chunks = processor.process(markdown, doc_id=1)

        content_chunk = None
        for chunk in chunks:
            if chunk.content == "内容":
                content_chunk = chunk
                break

        assert content_chunk is not None
        assert "第一章" in content_chunk.title_path
        assert "第一节" in content_chunk.title_path
        assert "第一小节" in content_chunk.title_path
