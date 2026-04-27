# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 数据模型模块

包含 WikiChunk、GlobalKG、AliasIndex、ChunkMap 四个核心模型。

Author: lhx
Date: 2026-04-23
"""

from app.service.wiki_knowledge.models.wiki_chunk import WikiChunk
from app.service.wiki_knowledge.models.global_kg import GlobalKG
from app.service.wiki_knowledge.models.alias_index import AliasIndex
from app.service.wiki_knowledge.models.chunk_map import ChunkMap

__all__ = [
    "WikiChunk",
    "GlobalKG",
    "AliasIndex",
    "ChunkMap",
]
