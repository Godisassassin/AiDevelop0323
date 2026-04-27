# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 切片映射模型

对应 chunk_map 表，连接知识节点与知识切片。
是关联大脑与肉体的桥梁，kg_id + chunk_id 为业务唯一键。

Author: lhx
Date: 2026-04-23
"""

from sqlalchemy import Column, String, Float

from common.model.BaseEntity import BaseEntity


class ChunkMap(BaseEntity):
    """切片映射模型，对应 chunk_map 表。

    连接知识节点与知识切片，是关联大脑与肉体的桥梁。
    kg_id + chunk_id 为业务唯一键（非复合主键，支持软删除）。

    Attributes:
        chunk_id: 切片ID
        kg_id: 知识节点ID
        weight: 关联权重
    """

    __tablename__ = "chunk_map"

    chunk_id = Column("chunk_id", String(36), nullable=False, index=True)
    kg_id = Column("kg_id", String(36), nullable=False, index=True)
    weight = Column("weight", Float, default=1.0)
