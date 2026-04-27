# -*- coding: utf-8 -*-
"""
Wiki 知识库 - API 端点测试

Author: lhx
Date: 2026-04-27
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.api.v1.endpoint.wiki_knowledge import router


class TestWikiKnowledgeAPI:
    """Wiki 知识库 API 端点测试。"""

    @pytest.fixture
    def client(self):
        """创建测试客户端。"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def mock_header_values(self):
        """模拟 header 值。"""
        return {
            "user-id": "test-user-001",
            "role": "admin",
            "org-id": "test-org-001",
        }

    def test_process_request_model(self):
        """测试 ProcessRequest 模型。"""
        from app.api.v1.endpoint.wiki_knowledge import ProcessRequest

        request = ProcessRequest(
            markdown_content="# 水杯清洗指南\n\n内容...",
            doc_id="doc-001",
            knowledge_id="kg-001",
        )
        assert request.markdown_content == "# 水杯清洗指南\n\n内容..."
        assert request.doc_id == "doc-001"
        assert request.knowledge_id == "kg-001"

    def test_retrieve_request_model(self):
        """测试 RetrieveRequest 模型。"""
        from app.api.v1.endpoint.wiki_knowledge import RetrieveRequest

        request = RetrieveRequest(
            query="如何清洗水杯？",
            knowledge_ids=["kg-001"],
            limit=10,
            top_k=3,
        )
        assert request.query == "如何清洗水杯？"
        assert request.knowledge_ids == ["kg-001"]
        assert request.limit == 10
        assert request.top_k == 3

    def test_retrieve_request_defaults(self):
        """测试 RetrieveRequest 默认值。"""
        from app.api.v1.endpoint.wiki_knowledge import RetrieveRequest

        request = RetrieveRequest(query="测试")
        assert request.knowledge_ids is None
        assert request.limit == 10
        assert request.top_k == 3


class TestProcessDocumentEndpoint:
    """process_document 端点测试。"""

    @pytest.fixture
    def client(self):
        """创建测试客户端。"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_process_endpoint_success(self, client, mock_header_values):
        """测试文档入库成功。"""
        with patch(
            "app.api.v1.endpoint.wiki_knowledge.get_header_value"
        ) as mock_get_header:
            # 模拟 header 返回值
            def get_header(s):
                return mock_header_values.get(s.replace("-", "_"))

            mock_get_header.side_effect = get_header

            with patch(
                "app.api.v1.endpoint.wiki_knowledge.WikiKnowledgePipeline"
            ) as MockPipeline:
                mock_pipeline = MagicMock()
                mock_pipeline.process_document = AsyncMock(
                    return_value={
                        "chunks": 5,
                        "entities": 10,
                        "alias": 12,
                        "new_kg": 3,
                    }
                )
                MockPipeline.return_value = mock_pipeline

                response = client.post(
                    "/process",
                    json={
                        "markdown_content": "# 测试文档",
                        "doc_id": "doc-001",
                    },
                    headers={
                        "user-id": "test-user",
                        "role": "admin",
                        "org-id": "test-org",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "success"
                assert data["data"]["chunks"] == 5
                assert data["data"]["entities"] == 10


class TestRetrieveEndpoint:
    """retrieve_knowledge 端点测试。"""

    @pytest.fixture
    def client(self):
        """创建测试客户端。"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_retrieve_endpoint_success(self, client, mock_header_values):
        """测试知识检索成功。"""
        with patch(
            "app.api.v1.endpoint.wiki_knowledge.get_header_value"
        ) as mock_get_header:
            def get_header(s):
                return mock_header_values.get(s.replace("-", "_"))

            mock_get_header.side_effect = get_header

            with patch(
                "app.api.v1.endpoint.wiki_knowledge.WikiKnowledgeRetriever"
            ) as MockRetriever:
                mock_retriever = MagicMock()
                mock_retriever.retrieve = AsyncMock(
                    return_value=MagicMock(
                        answer="清洗水杯的步骤：首先用清水冲洗。",
                        sources=[
                            {
                                "chunk_id": "chunk-1",
                                "title_path": "第一章 > 水杯清洗",
                                "score": 0.95,
                            }
                        ],
                        generated_at="2026-04-27T10:00:00",
                    )
                )
                MockRetriever.return_value = mock_retriever

                response = client.post(
                    "/retrieve",
                    json={
                        "query": "如何清洗水杯？",
                    },
                    headers={
                        "user-id": "test-user",
                        "role": "admin",
                        "org-id": "test-org",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "success"
                assert "清洗" in data["data"]["answer"]
                assert len(data["data"]["sources"]) == 1

    def test_retrieve_endpoint_with_params(self, client, mock_header_values):
        """测试带参数的知识检索。"""
        with patch(
            "app.api.v1.endpoint.wiki_knowledge.get_header_value"
        ) as mock_get_header:
            def get_header(s):
                return mock_header_values.get(s.replace("-", "_"))

            mock_get_header.side_effect = get_header

            with patch(
                "app.api.v1.endpoint.wiki_knowledge.WikiKnowledgeRetriever"
            ) as MockRetriever:
                mock_retriever = MagicMock()
                mock_retriever.retrieve = AsyncMock(
                    return_value=MagicMock(
                        answer="答案",
                        sources=[],
                        generated_at="2026-04-27T10:00:00",
                    )
                )
                MockRetriever.return_value = mock_retriever

                response = client.post(
                    "/retrieve",
                    json={
                        "query": "如何清洗水杯？",
                        "knowledge_ids": ["kg-001", "kg-002"],
                        "limit": 5,
                        "top_k": 2,
                    },
                    headers={
                        "user-id": "test-user",
                        "role": "admin",
                        "org-id": "test-org",
                    },
                )

                assert response.status_code == 200
                # 验证 retriever 被调用时传入了正确参数
                mock_retriever.retrieve.assert_called_once()
                call_kwargs = mock_retriever.retrieve.call_args.kwargs
                assert call_kwargs["knowledge_ids"] == ["kg-001", "kg-002"]
                assert call_kwargs["limit"] == 5
                assert call_kwargs["top_k"] == 2