# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 全局知识图谱模型

对应 global_kg 表，存储唯一的知识节点。
是知识库的大脑，承载实体和概念的标准名称与定义。

Author: lhx
Date: 2026-04-23
"""

from sqlalchemy import Column, String, Text

from common.model.BaseEntity import BaseEntity


class GlobalKG(BaseEntity):
    """全局知识图谱模型，对应 global_kg 表。

    存储唯一的知识节点，是知识库的大脑。
    承载实体和概念的标准名称与定义。

    Attributes:
        kg_id: 知识节点唯一标识 (UUID)
        standard_name: 标准名称
        description: 实体/概念定义描述
        category: 分类 (entity/concept)
    """

    __tablename__ = "global_kg"

    kg_id = Column("kg_id", String(36), nullable=False, unique=True, index=True)
    standard_name = Column("standard_name", String(100), nullable=False, index=True)
    description = Column("description", Text, nullable=True)
    category = Column("category", String(50), nullable=True)
