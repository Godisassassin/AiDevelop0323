# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 数据模型单元测试

测试 WikiChunk、GlobalKG、AliasIndex、ChunkMap 四个模型的字段定义和验证规则。

Author: lhx
Date: 2026-04-23

测试结果 (2026-04-24):
- ✅ test_tablename: PASSED (所有4个模型)
- ✅ test_inherits_base_entity: PASSED (所有4个模型)
- ✅ test_field_definitions: PASSED (所有4个模型)
- ❌ test_save_and_query: FAILED (SQLite 不支持 BigInteger，MySQL 环境待验证)
- ❌ test_pending_review_default: FAILED (SQLite 编码问题，MySQL 环境待验证)
- ❌ test_weight_default: FAILED (SQLite 编码问题，MySQL 环境待验证)

后续阶段待验证:
- 阶段二 (存储服务): 接 MySQL 后验证 CRUD 操作
- 阶段二 (存储服务): 验证 add_setting() 正确设置 create_by 字段
- 阶段二 (存储服务): 验证 Redis 缓存更新逻辑
- 阶段六 (流水线整合): 验证 document → chunk → extract → resolve → store 完整流程
"""

from pathlib import Path

# 添加 AIBackend 根目录到 sys.path
# Path(__file__) = test_models.py
# .parent = tests
# .parent = wiki_knowledge
# .parent = service
# .parent = app
# .parent = rag-pipeline-service
# .parent = AIBackend
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(ROOT_DIR))

from app.service.wiki_knowledge.models import WikiChunk, GlobalKG, AliasIndex, ChunkMap  # noqa: E402


class TestWikiChunk:
    """测试 WikiChunk 模型"""

    def test_tablename(self):
        """测试表名定义"""
        assert WikiChunk.__tablename__ == "wiki_chunks"

    def test_inherits_base_entity(self):
        """测试继承 BaseEntity"""
        from common.model.BaseEntity import BaseEntity

        assert issubclass(WikiChunk, BaseEntity)

    def test_field_definitions(self):
        """测试字段定义"""
        columns = {c.name for c in WikiChunk.__table__.columns}
        expected = {
            "id",
            "chunk_id",
            "doc_id",
            "title_path",
            "content",
            "summary",
            "parent_title",
            "sibling_titles",
            "create_at",
            "create_by",
            "update_at",
            "update_by",
            "delete_flag",
        }
        assert columns >= expected

    def test_save_and_query(self, db_session):
        """测试保存和查询"""
        chunk = WikiChunk()
        chunk.chunk_id = "test-chunk-001"
        chunk.doc_id = 123
        chunk.title_path = "第一章 > 第一节 > 标题"
        chunk.content = "这是测试内容"
        chunk.summary = "测试摘要"
        chunk.parent_title = "第一节"
        chunk.sibling_titles = '["标题2", "标题3"]'

        db_session.add(chunk)
        db_session.commit()

        result = (
            db_session.query(WikiChunk).filter_by(chunk_id="test-chunk-001").first()
        )
        assert result is not None
        assert result.doc_id == 123
        assert result.content == "这是测试内容"


class TestGlobalKG:
    """测试 GlobalKG 模型"""

    def test_tablename(self):
        """测试表名定义"""
        assert GlobalKG.__tablename__ == "global_kg"

    def test_inherits_base_entity(self):
        """测试继承 BaseEntity"""
        from common.model.BaseEntity import BaseEntity

        assert issubclass(GlobalKG, BaseEntity)

    def test_field_definitions(self):
        """测试字段定义"""
        columns = {c.name for c in GlobalKG.__table__.columns}
        expected = {
            "id",
            "kg_id",
            "standard_name",
            "description",
            "category",
            "create_at",
            "create_by",
            "update_at",
            "update_by",
            "delete_flag",
        }
        assert columns >= expected

    def test_save_and_query(self, db_session):
        """测试保存和查询"""
        kg = GlobalKG()
        kg.kg_id = "test-kg-001"
        kg.standard_name = "深度学习"
        kg.description = "深度学习是机器学习的分支"
        kg.category = "concept"

        db_session.add(kg)
        db_session.commit()

        result = db_session.query(GlobalKG).filter_by(kg_id="test-kg-001").first()
        assert result is not None
        assert result.standard_name == "深度学习"
        assert result.category == "concept"


class TestAliasIndex:
    """测试 AliasIndex 模型"""

    def test_tablename(self):
        """测试表名定义"""
        assert AliasIndex.__tablename__ == "alias_index"

    def test_inherits_base_entity(self):
        """测试继承 BaseEntity"""
        from common.model.BaseEntity import BaseEntity

        assert issubclass(AliasIndex, BaseEntity)

    def test_field_definitions(self):
        """测试字段定义"""
        columns = {c.name for c in AliasIndex.__table__.columns}
        expected = {
            "id",
            "alias_name",
            "kg_id",
            "pending_review",
            "create_at",
            "create_by",
            "update_at",
            "update_by",
            "delete_flag",
        }
        assert columns >= expected

    def test_save_and_query(self, db_session):
        """测试保存和查询"""
        alias = AliasIndex()
        alias.alias_name = "深度学习"
        alias.kg_id = "test-kg-001"
        alias.pending_review = False

        db_session.add(alias)
        db_session.commit()

        result = db_session.query(AliasIndex).filter_by(alias_name="深度学习").first()
        assert result is not None
        assert result.kg_id == "test-kg-001"
        assert result.pending_review is False

    def test_pending_review_default(self, db_session):
        """测试 pending_review 默认值"""
        alias = AliasIndex()
        alias.alias_name = "机器学习"
        alias.kg_id = "test-kg-002"

        db_session.add(alias)
        db_session.commit()

        result = db_session.query(AliasIndex).filter_by(alias_name="机器学习").first()
        assert result.pending_review is False


class TestChunkMap:
    """测试 ChunkMap 模型"""

    def test_tablename(self):
        """测试表名定义"""
        assert ChunkMap.__tablename__ == "chunk_map"

    def test_inherits_base_entity(self):
        """测试继承 BaseEntity"""
        from common.model.BaseEntity import BaseEntity

        assert issubclass(ChunkMap, BaseEntity)

    def test_field_definitions(self):
        """测试字段定义"""
        columns = {c.name for c in ChunkMap.__table__.columns}
        expected = {
            "id",
            "chunk_id",
            "kg_id",
            "weight",
            "create_at",
            "create_by",
            "update_at",
            "update_by",
            "delete_flag",
        }
        assert columns >= expected

    def test_save_and_query(self, db_session):
        """测试保存和查询"""
        chunk_map = ChunkMap()
        chunk_map.chunk_id = "test-chunk-001"
        chunk_map.kg_id = "test-kg-001"
        chunk_map.weight = 1.5

        db_session.add(chunk_map)
        db_session.commit()

        result = db_session.query(ChunkMap).filter_by(chunk_id="test-chunk-001").first()
        assert result is not None
        assert result.kg_id == "test-kg-001"
        assert result.weight == 1.5

    def test_weight_default(self, db_session):
        """测试 weight 默认值"""
        chunk_map = ChunkMap()
        chunk_map.chunk_id = "test-chunk-002"
        chunk_map.kg_id = "test-kg-002"

        db_session.add(chunk_map)
        db_session.commit()

        result = db_session.query(ChunkMap).filter_by(chunk_id="test-chunk-002").first()
        assert result.weight == 1.0
