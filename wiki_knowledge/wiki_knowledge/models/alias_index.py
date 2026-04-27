# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 同义词索引模型

对应 alias_index 表，用于将用户的口语转化为 kg_id。
是检索的路标，建立别名/同义词到知识节点的映射。

Author: lhx
Date: 2026-04-23
"""

from sqlalchemy import Column, String, Boolean

from common.model.BaseEntity import BaseEntity


class AliasIndex(BaseEntity):
    """同义词索引模型，对应 alias_index 表。

    用于将用户的口语转化为 kg_id，是检索的路标。
    建立别名/同义词到知识节点的映射。

    Attributes:
        alias_name: 别名/同义词名称
        kg_id: 关联的知识节点ID
        pending_review: 是否待审核 (软关联时为 True)
    """

    __tablename__ = "alias_index"

    alias_name = Column(
        "alias_name", String(100), nullable=False, unique=True, index=True
    )
    kg_id = Column("kg_id", String(36), nullable=False, index=True)
    pending_review = Column("pending_review", Boolean, default=False)
