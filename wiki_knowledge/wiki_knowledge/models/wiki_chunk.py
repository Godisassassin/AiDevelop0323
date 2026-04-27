# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 知识切片模型

对应 wiki_chunks 表，存储最小粒度的文档原文。
是 Wiki 知识库的核心存储单元，父级标题和同级标题用于上下文感知特征提取。

Author: lhx
Date: 2026-04-23
"""

from sqlalchemy import Column, BigInteger, String, Text

from common.model.BaseEntity import BaseEntity


class WikiChunk(BaseEntity):
    """知识切片模型，对应 wiki_chunks 表。

    存储最小粒度的文档原文，是 Wiki 知识库的核心存储单元。
    父级标题和同级标题用于上下文感知特征提取。

    Attributes:
        chunk_id: 切片唯一标识 (UUID)
        doc_id: 文档ID
        title_path: 标题路径
        content: 切片内容
        summary: 摘要
        parent_title: 父级标题
        sibling_titles: 同级标题列表 (JSON 格式)
    """

    __tablename__ = "wiki_chunks"

    chunk_id = Column("chunk_id", String(36), nullable=False, unique=True, index=True)
    doc_id = Column("doc_id", BigInteger, nullable=False, index=True)
    title_path = Column("title_path", Text, nullable=False)
    content = Column("content", Text, nullable=False)
    summary = Column("summary", String(500), nullable=True)
    parent_title = Column("parent_title", String(200), nullable=True)
    sibling_titles = Column("sibling_titles", Text, nullable=True)
