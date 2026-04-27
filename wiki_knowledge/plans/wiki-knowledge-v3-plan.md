Wiki 知识库功能拓展 - 代码实现级计划书

需求来源：notebook/知识链路-wiki.md
遵循规范：ai-obr-dev 技能（/ai-obr-dev）
核心约束：不改变原有代码，通过扩展点新增功能
产出路径：plans/wiki-knowledge-v2-plan.md


---

一、现状分析

1.1 当前架构

当前无 Wiki 知识库功能，依赖传统 RAG：
- 传统 RAG 采用向量相似度检索
- 切片组织为独立片段，无关联标签
- 知识组织为扁平结构
- 答案生成直接返回切片
1.2 当前问题

问题
描述
检索精度不足
向量相似度无法精准定位实体和概念
上下文丢失
切片独立无关联，无法理解文档层级结构
同义词处理弱
用户口语化表达难以匹配标准术语
答案质量低
直接返回切片，缺乏整合生成能力

1.3 关键数据流

组件
存储
集合/表
文档原始内容
阿里云 OSS
源文件存储
知识切片

MongoDB + Meilisearch

wiki_chunks
全局知识图谱
MySQL
global_kg
别名索引
MySQL + Redis
alias_index + 缓存
切片映射
MySQL
chunk_map
前端查询 /api/v1/retrieve/unified
    ↓
Meilisearch Client 并发查询
    ↓
┌──────────────────────────────────────┐
│  查询1: index="rag_chunks"          │
│         query="水杯"                │
├──────────────────────────────────────┤
│  查询2: index="wiki_chunks"         │
│         query="水杯"                 │
└──────────────────────────────────────┘
    ↓
合并结果，按 score 排序
    ↓
返回统一响应（含 source 标记）


---

二、目标

将传统 RAG 升级为 Wiki 知识库，实现"逻辑关联，物理隔离"：

性能监控数据 → Agent 自动分析 → Agent 自动优化技能/提示词 → 验证效果

2.1 具体目标

1. 文档入库流水线：将 Markdown 文档转化为带关联标签的结构化切片
2. 实体对齐与冲突处理：新实体经过候选筛选 → LLM 裁决 → 存储/关联
3. 多路精准检索：路径匹配 + 实体导航，而非向量相似度
4. 动作粗筛：通过动作词匹配过滤并排序切片
5. 答案生成：LLM 基于 Top 3 切片生成答案并标注溯源
2.2 与现有 RAG 的区别

维度
传统 RAG
Wiki 知识库
检索方式
向量相似度
实体中心导航 + 关键词匹配
切片组织
独立片段
带关联标签的结构化切片
知识组织
扁平
网状（Entity-Concept 关系）
答案生成
直接返回切片
LLM 整合切片生成答案


---

三、方案设计

3.1 核心思路

新增独立模块 service/wiki_knowledge/，包含：
- 文档处理流水线（切片 → 特征提取 → 实体对齐 → 存储）
- 检索与答案生成（查询解析 → 多路匹配 → 动作过滤 → 答案生成）
- 审核服务（别名审核）
3.2 架构图

3.2.1 文档入库流水线架构

文档上传
    ↓
WikiChunkProcessor（切片处理）
    ↓
ContextAwareExtractor（特征提取）
    ↓
EntityResolver（实体对齐）
    ↓
WikiChunkStore（存储）

3.2.2 检索与答案生成架构

用户查询
    ↓
QueryParser（查询解析）
    ↓
MultiMatchRetriever（多路精准匹配）
    ↓
ActionFilter（动作粗筛）
    ↓
AnswerSynthesizer（答案生成）
    ↓
返回答案 + 溯源

3.2.3 存储架构

┌─────────────────────────────────────────────────────────────┐
│                      Wiki 知识库存储架构                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │   MySQL     │    │ MongoDB     │    │   Redis     │      │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤      │
│  │  chunk_map  │    │ wiki_chunks │    │ Alias_Index │      │
│  │ global_kg   │    │ 全文检索     │    │   缓存      │      │
│  │ alias_index │    └─────────────┘    │             │      │   
│  │             │    │ 同步到       │    │             │      │
│  │             │    │ Meilisearch │    │             │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                    ┌───────▼───────┐                        │
│                    │  阿里云 OSS   │                        │
│                    │  源文件存储    │                        │
│                    └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
存储分工说明：
- MongoDB ：wiki_chunks（知识切片），提供高速全文检索，需同步到Meilisearch
- MySQL：global_kg（全局知识图谱）、alias_index（同义词索引）、chunk_map（切片映射）
- Redis：别名索引缓存、热点数据缓存
- 阿里云 OSS：源文件存储
3.3 数据库设计

3.3.1 Wiki_Chunks（知识切片表）

文件：service/wiki_knowledge/models/wiki_chunk.py

class WikiChunk(BaseEntity):
    """知识切片模型，对应 wiki_chunks 表。

    存储最小粒度的文档原文，是 Wiki 知识库的核心存储单元。
    父级标题和同级标题用于上下文感知特征提取。
    继承 BaseEntity：id (BigInteger), create_at, create_by, update_at, update_by, delete_flag
    """
    __tablename__ = "wiki_chunks"

    chunk_id = Column("chunk_id", String(36), nullable=False, unique=True, index=True)
    doc_id = Column("doc_id", BigInteger, nullable=False, index=True)
    title_path = Column("title_path", Text, nullable=False)
    content = Column("content", Text, nullable=False)
    summary = Column("summary", String(500), nullable=True)
    parent_title = Column("parent_title", String(200), nullable=True)
    sibling_titles = Column("sibling_titles", Text, nullable=True)

3.3.2 Global_KG（全局知识图谱表）

文件：service/wiki_knowledge/models/global_kg.py

class GlobalKG(BaseEntity):
    """全局知识图谱模型，对应 global_kg 表。

    存储唯一的知识节点，是知识库的大脑。
    继承 BaseEntity：id (BigInteger), create_at, create_by, update_at, update_by, delete_flag
    """
    __tablename__ = "global_kg"

    kg_id = Column("kg_id", String(36), nullable=False, unique=True, index=True)
    standard_name = Column("standard_name", String(100), nullable=False, index=True)
    description = Column("description", Text, nullable=True)
    category = Column("category", String(50), nullable=True)

3.3.3 Alias_Index（同义词索引表）

文件：service/wiki_knowledge/models/alias_index.py

class AliasIndex(BaseEntity):
    """同义词索引模型，对应 alias_index 表。

    用于将用户的口语转化为 kg_id，是检索的路标。
    继承 BaseEntity：id (BigInteger), create_at, create_by, update_at, update_by, delete_flag
    """
    __tablename__ = "alias_index"

    alias_name = Column("alias_name", String(100), nullable=False, unique=True, index=True)
    kg_id = Column("kg_id", String(36), nullable=False, index=True)
    pending_review = Column("pending_review", Boolean, default=False)

3.3.4 Chunk_Map（切片映射表）

文件：service/wiki_knowledge/models/chunk_map.py

class ChunkMap(BaseEntity):
    """切片映射模型，对应 chunk_map 表。

    连接知识节点与知识切片，是关联大脑与肉体的桥梁。
    kg_id + chunk_id 为业务唯一键（非复合主键，支持软删除）。
    继承 BaseEntity：id (BigInteger), create_at, create_by, update_at, update_by, delete_flag
    """
    __tablename__ = "chunk_map"

    chunk_id = Column("chunk_id", String(36), nullable=False, index=True)
    kg_id = Column("kg_id", String(36), nullable=False, index=True)
    weight = Column("weight", Float, default=1.0)

3.3.5 表关系说明

global_kg (核心知识节点)
    ↓ 1:N
alias_index (同义词索引)  [alias_name -> kg_id]
    ↓ N:1
chunk_map (切片映射)  [kg_id, chunk_id]
    ↓ N:1
wiki_chunks (知识切片)  [chunk_id]


---

四、修改点清单

4.1 新增文件

4.1.1 数据库模型（4个文件）

文件路径
说明
AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/init.py
模型模块导出
AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/wiki_chunk.py
WikiChunk 模型 
AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/global_kg.py
GlobalKG 模型 
AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/alias_index.py
AliasIndex 模型
AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/chunk_map.py
ChunkMap 模型 

4.1.2 文档处理流水线（5个文件）

文件路径
说明
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/init.py 
 处理器模块导出 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/chunk_processor.py 
 WikiChunkProcessor：切片处理 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/context_extractor.py 
 ContextAwareExtractor：特征提取 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/entity_resolver.py 
 EntityResolver：实体对齐 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/chunk_store.py 
 WikiChunkStore：存储服务 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/pipeline.py 
 WikiKnowledgePipeline：流水线入口 

 ContextAwareExtractor

文件：service/wiki_knowledge/processor/context_extractor.py

"""上下文感知特征提取器。

将切片内容、父级标题、同级标题同时输入 LLM，提取实体、概念和同义词。
"""
import json
from dataclasses import dataclass, field
from typing import Optional

from app.service.pooling_client.embedding_client import get_embedding


@dataclass
class ExtractionResult:
    """特征提取结果。

    Attributes:
        entities: 实体列表（具象名词：API名称、组件名、错误码、参数等）
        concepts: 概念列表（抽象名词：业务逻辑、设计思想、协议原理等）
        synonyms: 同义词字典（标准名 -> 同义词列表）
    """
    entities: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    synonyms: dict[str, list[str]] = field(default_factory=dict)


class ContextAwareExtractor:
    """上下文感知特征提取器。

    利用 LLM 提取切片中的实体、概念，并生成同义词扩展。
    上下文信息（父级标题、同级标题）帮助 LLM 准确理解切片语义。

    Methods:
        extract: 提取切片特征
        _build_context_prompt: 构建包含上下文的 prompt
        _call_llm: 调用 LLM 服务
    """

    # LLM Prompt 模板
    EXTRACTION_PROMPT = """## Context
当前切片：
{content}

父级标题：{parent_title}

同级标题：{sibling_titles}

## Task
从上述切片中提取：
1. 实体 (Entities)：具象名词（API名称、组件名、错误码、特定参数）
2. 概念 (Concepts)：抽象名词（业务逻辑、设计思想、协议原理）
3. 同义词扩展：为每个实体/概念生成3-5个潜在搜索关键词

## Output Format
JSON格式（不包含任何解释性文字）：
{{
  "entities": ["实体1", "实体2"],
  "concepts": ["概念1", "概念2"],
  "synonyms": {{
    "实体1": ["同义词1", "同义词2"],
    "概念1": ["同义词1", "同义词2"]
  }}
}}"""

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 服务。

        使用平台封装的 unified_agent_invoke 进行 LLM 调用。

        Args:
            prompt: 提示词

        Returns:
            LLM 响应文本
        """
        from app.config.config import settings
        from app.services.llm_chat.unified_agent import unified_agent_invoke
        from app.services.llm_chat.request import UnifiedAgentRequest

        # 构建请求
        request = UnifiedAgentRequest(
            query=prompt,
            project_id=settings.get("WIKI_KNOWLEDGE_PROJECT_ID"),
        )

        # 调用统一 Agent
        result = await unified_agent_invoke(request, agent_context={})

        return result.get("answer", "")

    async def extract(self, chunk_result, llm_model: str = "deepseek") -> ExtractionResult:
        """提取切片特征。

        Args:
            chunk_result: WikiChunkProcessor 返回的切片结果
            llm_model: 使用的 LLM 模型（已废弃，改为从配置读取）

        Returns:
            ExtractionResult：包含实体、概念、同义词
        """
        prompt = self._build_context_prompt(chunk_result)

        # 调用 LLM
        response = await self._call_llm(prompt)

        # 解析 JSON 响应
        try:
            result = json.loads(response)
            return ExtractionResult(
                entities=result.get("entities", []),
                concepts=result.get("concepts", []),
                synonyms=result.get("synonyms", {})
            )
        except json.JSONDecodeError:
            # LLM 返回格式异常，返回空结果
            return ExtractionResult()

    def _build_context_prompt(self, chunk_result) -> str:
        """构建包含上下文的 prompt。

        Args:
            chunk_result: 切片结果

        Returns:
            格式化后的 prompt 字符串
        """
        # 限制内容长度，避免超出 LLM 上下文
        content = chunk_result.content[:2000] if chunk_result.content else ""
        parent_title = chunk_result.parent_title or "无"
        sibling_titles = ", ".join(chunk_result.sibling_titles[:5]) if chunk_result.sibling_titles else "无"

        return self.EXTRACTION_PROMPT.format(
            content=content,
            parent_title=parent_title,
            sibling_titles=sibling_titles
        )

 EntityResolver

文件：service/wiki_knowledge/processor/entity_resolver.py

"""实体对齐与冲突处理器。

处理新实体与现有实体的匹配、裁决和存储。
"""
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.service.pooling_client.embedding_client import get_embedding


class ResolutionType(Enum):
    """裁决结果类型。"""
    ALIAS = "alias"           # 自动对齐：置信度 >= 0.85
    SOFT_LINK = "soft_link"   # 软关联待审核：0.6 <= 置信度 < 0.85
    NEW = "new"               # 独立：置信度 < 0.6
    RELATED = "related"       # 关联：建立相关链接（不变）


@dataclass
class ResolutionResult:
    """实体裁决结果。

    Attributes:
        original_name: 原始实体名
        resolution_type: 裁决类型
        kg_id: 关联的知识节点ID（新或已有）
        confidence: 置信度 (0-1)
        pending_review: 是否待审核（仅 SOFT_LINK 时为 True）
    """
    original_name: str
    resolution_type: ResolutionType
    kg_id: str
    confidence: float
    pending_review: bool = False


class EntityResolver:
    """实体对齐与冲突处理器。

    当提取出新实体时，执行候选筛选和 LLM 裁决。

    裁决规则：
    - S >= 0.85：自动对齐，合并到现有实体的同义词库
    - 0.6 <= S < 0.85：软关联，标记待审核
    - S < 0.6：判定为新实体，创建独立的 kg_id

    Methods:
        resolve: 裁决新实体
        _candidate_filter: 候选筛选
        _llm_judge: LLM 裁决
        _call_llm: 调用 LLM 服务
    """

    # LLM 裁决 Prompt
    JUDGE_PROMPT = """## Task
对比两个实体，判断它们是否等价。

实体 A：{entity_a_name}
定义：{entity_a_def}

实体 B：{entity_b_name}
定义：{entity_b_def}

## Evaluation Rules
1. 全等关系（如 Client 和 客户端）-> 置信度 >= 0.9
2. 包含关系（如 支付 和 微信支付）-> 置信度 0.6-0.7
3. 语义相关但对象不同 -> 置信度 < 0.3

## Output Format
JSON格式（不包含任何解释性文字）：
{{
  "confidence": 0.0-1.0,
  "reason": "判断理由"
}}"""

    # 裁决阈值
    THRESHOLD_AUTO_ALIGN = 0.85  # 自动对齐
    THRESHOLD_SOFT_LINK = 0.6    # 软关联（需人工审核）
    MAX_CANDIDATES = 10          # Top N 候选

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 服务。

        使用平台封装的 unified_agent_invoke 进行 LLM 调用。

        Args:
            prompt: 提示词

        Returns:
            LLM 响应文本
        """
        from app.config.config import settings
        from app.services.llm_chat.unified_agent import unified_agent_invoke
        from app.services.llm_chat.request import UnifiedAgentRequest

        # 构建请求
        request = UnifiedAgentRequest(
            query=prompt,
            project_id=settings.get("WIKI_KNOWLEDGE_PROJECT_ID"),
        )

        # 调用统一 Agent
        result = await unified_agent_invoke(request, agent_context={})

        return result.get("answer", "")

    async def resolve(
        self,
        entity_name: str,
        entity_def: str,
        candidates: list[dict]
    ) -> ResolutionResult:
        """裁决新实体。

        Args:
            entity_name: 待裁决的实体名
            entity_def: 实体定义（来自切片内容）
            candidates: 候选实体列表（从别名索引查询）

        Returns:
            ResolutionResult：裁决结果
        """
        # 如果没有候选实体，直接创建新节点
        if not candidates:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.NEW,
                kg_id="",  # 需要调用方创建
                confidence=0.0,
                pending_review=False
            )

        # 获取最佳候选的置信度
        best_candidate = candidates[0]
        confidence, _ = await self._llm_judge(
            entity_a=(entity_name, entity_def),
            entity_b=(best_candidate["name"], best_candidate.get("description", ""))
        )

        # 根据置信度确定裁决类型
        if confidence >= self.THRESHOLD_AUTO_ALIGN:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.ALIAS,
                kg_id=best_candidate["kg_id"],
                confidence=confidence,
                pending_review=False
            )
        elif confidence >= self.THRESHOLD_SOFT_LINK:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.SOFT_LINK,
                kg_id=best_candidate["kg_id"],
                confidence=confidence,
                pending_review=True
            )
        else:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.NEW,
                kg_id="",
                confidence=confidence,
                pending_review=False
            )

    async def _candidate_filter(self, entity_name: str) -> list[dict]:
        """候选筛选。

        在别名索引中检索名称相似或已有同义词覆盖的候选实体。

        Args:
            entity_name: 实体名

        Returns:
            Top N 候选实体列表，每个包含 kg_id, name, description
        """
        # TODO: 实现 MongoDB 查询 Alias_Index
        # 实现逻辑：从 alias_index 表查询名称相似或同义词匹配的候选
        pass

    async def _llm_judge(
        self,
        entity_a: tuple[str, str],
        entity_b: tuple[str, str]
    ) -> tuple[float, str]:
        """LLM 裁决。

        Args:
            entity_a: (名称, 定义)
            entity_b: (名称, 定义)

        Returns:
            (置信度, 判断理由)
        """
        prompt = self.JUDGE_PROMPT.format(
            entity_a_name=entity_a[0],
            entity_a_def=entity_a[1],
            entity_b_name=entity_b[0],
            entity_b_def=entity_b[1]
        )

        response = await self._call_llm(prompt)

        try:
            result = json.loads(response)
            return result.get("confidence", 0.0), result.get("reason", "")
        except json.JSONDecodeError:
            return 0.0, "JSON 解析失败"

WikiChunkStore

文件：service/wiki_knowledge/processor/chunk_store.py

"""知识切片存储服务。

负责将处理好的切片和实体写入 MySQL 数据库，并更新 Redis 缓存。
"""
import json
import uuid
from typing import Optional

from common.db.database import SQLUnitOfWork
from common.utils.base_entity_setting import add_setting

from app.service.wiki_knowledge.models.wiki_chunk import WikiChunk
from app.service.wiki_knowledge.models.global_kg import GlobalKG
from app.service.wiki_knowledge.models.alias_index import AliasIndex
from app.service.wiki_knowledge.models.chunk_map import ChunkMap


class WikiChunkStore:
    """知识切片存储器。

    封装 Wiki_Chunks、Global_KG、Alias_Index、Chunk_Map 的写入逻辑。
    使用 SQLUnitOfWork 保证事务一致性。
    别名写入后自动更新 Redis 缓存。

    Methods:
        save_chunk: 保存切片
        save_kg: 保存知识节点
        save_alias: 保存别名（自动更新 Redis）
        save_chunk_map: 保存切片映射
        get_alias_candidates: 获取别名候选实体
        _update_redis_cache: 更新 Redis 缓存
    """

    # Redis 缓存配置
    REDIS_ALIAS_CACHE_KEY = "wiki:alias_index"
    REDIS_ALIAS_CACHE_TTL = 3600 * 24  # 24小时

    def save_chunk(
        self,
        chunk_id: str,
        doc_id: str,
        title_path: str,
        content: str,
        summary: str,
        parent_title: Optional[str],
        sibling_titles: list[str],
        knowledge_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> WikiChunk:
        """保存知识切片。

        Args:
            chunk_id: 切片唯一标识
            doc_id: 文档ID
            title_path: 标题路径
            content: 切片内容
            summary: 摘要
            parent_title: 父级标题
            sibling_titles: 同级标题列表
            knowledge_id: 知识库ID（可选）
            user_id: 操作人ID（用于 BaseEntity 字段）

        Returns:
            WikiChunk 实例
        """
        wiki_chunk = WikiChunk()
        wiki_chunk.chunk_id = chunk_id
        wiki_chunk.doc_id = doc_id
        wiki_chunk.title_path = title_path
        wiki_chunk.content = content
        wiki_chunk.summary = summary
        wiki_chunk.parent_title = parent_title
        wiki_chunk.sibling_titles = json.dumps(sibling_titles) if sibling_titles else None

        if user_id:
            add_setting(wiki_chunk, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(wiki_chunk)

        return wiki_chunk

    def save_kg(
        self,
        standard_name: str,
        description: str,
        category: str,
        user_id: Optional[str] = None
    ) -> str:
        """保存知识节点到 Global_KG。

        Args:
            standard_name: 标准名称
            description: 实体定义
            category: 实体分类
            user_id: 操作人ID

        Returns:
            kg_id：新创建的知识节点ID
        """
        kg_id = str(uuid.uuid4())
        global_kg = GlobalKG()
        global_kg.kg_id = kg_id
        global_kg.standard_name = standard_name
        global_kg.description = description
        global_kg.category = category

        if user_id:
            add_setting(global_kg, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(global_kg)

        return kg_id

    def save_alias(
        self,
        alias_name: str,
        kg_id: str,
        pending_review: bool = False,
        user_id: Optional[str] = None
    ) -> AliasIndex:
        """保存别名到 Alias_Index。

        Args:
            alias_name: 别名/同义词
            kg_id: 知识节点ID
            pending_review: 是否待审核（软关联）
            user_id: 操作人ID

        Returns:
            AliasIndex 实例
        """
        alias = AliasIndex()
        alias.alias_name = alias_name
        alias.kg_id = kg_id
        alias.pending_review = pending_review

        if user_id:
            add_setting(alias, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(alias)

        # 更新 Redis 缓存
        self._update_redis_cache(alias_name, kg_id, pending_review)

        return alias

    def save_chunk_map(
        self,
        chunk_id: str,
        kg_id: str,
        weight: float = 1.0,
        user_id: Optional[str] = None
    ) -> ChunkMap:
        """保存切片与知识节点的映射。

        Args:
            chunk_id: 切片ID
            kg_id: 知识节点ID
            weight: 关联权重
            user_id: 操作人ID

        Returns:
            ChunkMap 实例
        """
        chunk_map = ChunkMap()
        chunk_map.chunk_id = chunk_id
        chunk_map.kg_id = kg_id
        chunk_map.weight = weight

        if user_id:
            add_setting(chunk_map, user_id)

        with SQLUnitOfWork() as uow:
            uow.session.add(chunk_map)

        return chunk_map

    def get_alias_candidates(self, entity_name: str) -> list[dict]:
        """获取别名候选实体。

        优先从 Redis 缓存查询，缓存未命中时查询 MySQL。

        Args:
            entity_name: 实体名

        Returns:
            候选实体列表，每个包含 kg_id, name, description
        """
        # 尝试从 Redis 缓存获取
        redis_result = self._get_from_redis_cache(entity_name)
        if redis_result:
            return redis_result

        # 缓存未命中，查询 MySQL
        with SQLUnitOfWork() as uow:
            aliases = uow.session.query(AliasIndex).filter(
                AliasIndex.alias_name == entity_name,
                AliasIndex.delete_flag == False
            ).limit(10).all()

            if not aliases:
                return []

            # 获取关联的 GlobalKG 信息
            candidates = []
            for alias in aliases:
                kg = uow.session.query(GlobalKG).filter(
                    GlobalKG.kg_id == alias.kg_id,
                    GlobalKG.delete_flag == False
                ).first()

                candidates.append({
                    "kg_id": alias.kg_id,
                    "name": alias.alias_name,
                    "description": kg.description if kg else ""
                })

            return candidates

    def _update_redis_cache(
        self,
        alias_name: str,
        kg_id: str,
        pending_review: bool
    ) -> None:
        """更新 Redis 缓存。

        Args:
            alias_name: 别名名称
            kg_id: 知识节点ID
            pending_review: 是否待审核
        """
        try:
            import redis
            from app.config.config import settings

            redis_config = settings.get("REDIS")
            redis_client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password")
            )

            # 使用 Hash 存储，field 为 alias_name
            cache_data = {
                "kg_id": kg_id,
                "pending_review": str(pending_review)
            }
            redis_client.hset(self.REDIS_ALIAS_CACHE_KEY, alias_name, json.dumps(cache_data))
            redis_client.expire(self.REDIS_ALIAS_CACHE_KEY, self.REDIS_ALIAS_CACHE_TTL)
        except Exception as e:
            # Redis 更新失败不影响主流程，仅记录日志
            import logging
            logging.warning(f"Redis 缓存更新失败: {e}")

    def _get_from_redis_cache(self, alias_name: str) -> Optional[list[dict]]:
        """从 Redis 缓存获取别名信息。

        Args:
            alias_name: 别名名称

        Returns:
            缓存的候选实体列表，未命中返回 None
        """
        try:
            import redis
            from app.config.config import settings

            redis_config = settings.get("REDIS")
            redis_client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password")
            )

            cached = redis_client.hget(self.REDIS_ALIAS_CACHE_KEY, alias_name)
            if cached:
                data = json.loads(cached)
                return [{
                    "kg_id": data["kg_id"],
                    "name": alias_name,
                    "description": ""
                }]
        except Exception as e:
            import logging
            logging.warning(f"Redis 缓存查询失败: {e}")

        return None

Pipeline
文件：service/wiki_knowledge/processor/pipeline.py

"""Wiki 知识库文档入库流水线入口。

整合切片处理、特征提取、实体对齐和存储的完整流程。
"""
from typing import Optional

from app.service.wiki_knowledge.processor.chunk_processor import (
    WikiChunkProcessor,
    ChunkResult
)
from app.service.wiki_knowledge.processor.context_extractor import (
    ContextAwareExtractor,
    ExtractionResult
)
from app.service.wiki_knowledge.processor.entity_resolver import (
    EntityResolver,
    ResolutionResult,
    ResolutionType
)
from app.service.wiki_knowledge.processor.chunk_store import WikiChunkStore


class WikiKnowledgePipeline:
    """Wiki 知识库文档入库流水线。

    整合切片处理、特征提取、实体对齐和存储。

    Methods:
        process_document: 处理文档并入库
    """

    def __init__(self):
        """初始化流水线各组件。"""
        self.processor = WikiChunkProcessor()
        self.extractor = ContextAwareExtractor()
        self.resolver = EntityResolver()
        self.store = WikiChunkStore()

    async def process_document(
        self,
        markdown_content: str,
        doc_id: str,
        knowledge_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> dict:
        """处理文档并入库。

        Args:
            markdown_content: Markdown 格式的文档内容
            doc_id: 文档唯一标识
            knowledge_id: 知识库ID（可选，用于关联）
            user_id: 操作人ID

        Returns:
            处理结果统计（切片数、实体数等）
        """
        # Step 1: 切片处理
        chunks = self.processor.process(markdown_content, doc_id)

        # 统计结果
        stats = {"chunks": 0, "entities": 0, "alias": 0, "new_kg": 0}

        # Step 2: 遍历切片进行特征提取和实体对齐
        for chunk in chunks:
            # 保存切片
            self.store.save_chunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                title_path=chunk.title_path,
                content=chunk.content,
                summary=chunk.summary,
                parent_title=chunk.parent_title,
                sibling_titles=chunk.sibling_titles,
                knowledge_id=knowledge_id,
                user_id=user_id
            )
            stats["chunks"] += 1

            # 特征提取
            extraction = await self.extractor.extract(chunk)

            # 实体对齐与存储
            for entity in extraction.entities + extraction.concepts:
                # 候选筛选
                candidates = self.store.get_alias_candidates(entity)

                # LLM 裁决
                resolution = await self.resolver.resolve(
                    entity_name=entity,
                    entity_def=chunk.content[:500],
                    candidates=candidates
                )

                # 根据裁决结果处理
                if resolution.resolution_type == ResolutionType.NEW:
                    # 创建新知识节点
                    kg_id = self.store.save_kg(
                        standard_name=entity,
                        description=chunk.content[:200],
                        category="entity" if entity in extraction.entities else "concept",
                        user_id=user_id
                    )
                    stats["new_kg"] += 1
                else:
                    kg_id = resolution.kg_id

                # 保存别名（带待审核标记）
                self.store.save_alias(
                    alias_name=entity,
                    kg_id=kg_id,
                    pending_review=resolution.pending_review,
                    user_id=user_id
                )
                stats["alias"] += 1

                # 保存切片与知识节点的映射
                self.store.save_chunk_map(
                    chunk_id=chunk.chunk_id,
                    kg_id=kg_id,
                    weight=1.0,
                    user_id=user_id
                )
                stats["entities"] += 1

            # 处理同义词扩展
            for standard_name, synonyms in extraction.synonyms.items():
                # 获取标准名对应的 kg_id
                candidates = self.store.get_alias_candidates(standard_name)
                if candidates:
                    kg_id = candidates[0]["kg_id"]
                    for synonym in synonyms:
                        self.store.save_alias(
                            alias_name=synonym,
                            kg_id=kg_id,
                            pending_review=False,
                            user_id=user_id
                        )

        return stats
4.1.3 检索与答案生成（5个文件）

文件路径
说明
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/init.py 
 检索模块导出 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/query_parser.py 
 QueryParser：查询解析 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/multi_matcher.py 
 MultiMatchRetriever：多路匹配 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/action_filter.py 
 ActionFilter：动作粗筛 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/answer_synthesizer.py 
 AnswerSynthesizer：答案生成 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/wiki_retriever.py 
 WikiKnowledgeRetriever：检索入口 

4.1.4 审核服务（1个文件）

文件路径
说明
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/review/init.py 
 审核模块导出 
 AIBackend/rag-pipeline-service/app/service/wiki_knowledge/review/alias_review.py 
 AliasReviewService：别名审核服务 

4.1.5 API 端点（2个文件）

文件路径
说明
AIBackend/ai-platform-service/app/api/v1/endpoint/wiki_knowledge.py
文档入库 + 知识检索 API
AIBackend/ai-platform-service/app/api/v1/endpoint/wiki_knowledge_review.py
别名审核 API

4.2 修改文件

文件路径
修改内容
AIBackend/ai-platform-service/app/api/v1/api.py
添加 wiki_knowledge 和 wiki_knowledge_review 路由注册
AIBackend/ai-platform-service/app/service/knowledge/knowledge.py
新增 get_knowledge_permission、get_available_knowledge_list 方法调用

4.3 需新增的方法

类/模块
方法
说明
KnowledgeServer
get_knowledge_permission(org_id, knowledge_id, role, user_id)
确认是否存在，用于权限校验
KnowledgeServer
get_available_knowledge_list(user_id, role, org_id)
确认是否存在，获取用户可访问知识库列表
MultiMatchRetriever
_path_match(target, knowledge_ids)
路径匹配（当前是 pass）
MultiMatchRetriever
_entity_navigate(target, knowledge_ids)
实体导航（当前是 pass）
EntityResolver
_candidate_filter(entity_name)
候选筛选（当前是 pass）

4.4 数据库迁移

-- 创建 wiki_chunks 表
CREATE TABLE wiki_chunks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chunk_id VARCHAR(36) NOT NULL UNIQUE,
    doc_id BIGINT NOT NULL,
    title_path TEXT NOT NULL,
    content TEXT NOT NULL,
    summary VARCHAR(500),
    parent_title VARCHAR(200),
    sibling_titles TEXT,
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    create_by VARCHAR(64),
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    update_by VARCHAR(64),
    delete_flag TINYINT DEFAULT 0,
    INDEX idx_doc_id (doc_id),
    FULLTEXT INDEX ft_title_path (title_path)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建 global_kg 表
CREATE TABLE global_kg (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kg_id VARCHAR(36) NOT NULL UNIQUE,
    standard_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    create_by VARCHAR(64),
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    update_by VARCHAR(64),
    delete_flag TINYINT DEFAULT 0,
    INDEX idx_standard_name (standard_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建 alias_index 表
CREATE TABLE alias_index (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alias_name VARCHAR(100) NOT NULL UNIQUE,
    kg_id VARCHAR(36) NOT NULL,
    pending_review TINYINT DEFAULT 0,
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    create_by VARCHAR(64),
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    update_by VARCHAR(64),
    delete_flag TINYINT DEFAULT 0,
    INDEX idx_kg_id (kg_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建 chunk_map 表
CREATE TABLE chunk_map (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chunk_id VARCHAR(36) NOT NULL,
    kg_id VARCHAR(36) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    create_by VARCHAR(64),
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    update_by VARCHAR(64),
    delete_flag TINYINT DEFAULT 0,
    INDEX idx_chunk_id (chunk_id),
    INDEX idx_kg_id (kg_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


---

五、目录结构

5.1 新增文件清单

AIBackend/ai-platform-service/app/
├── service/wiki_knowledge/
│   ├── init.py
│   ├── models/
│   │   ├── init.py
│   │   ├── wiki_chunk.py      # WikiChunk 模型
│   │   ├── global_kg.py       # GlobalKG 模型
│   │   ├── alias_index.py     # AliasIndex 模型
│   │   └── chunk_map.py       # ChunkMap 模型
│   ├── processor/
│   │   ├── init.py
│   │   ├── chunk_processor.py      # WikiChunkProcessor：切片处理
│   │   ├── context_extractor.py    # ContextAwareExtractor：特征提取
│   │   ├── entity_resolver.py      # EntityResolver：实体对齐
│   │   ├── chunk_store.py          # WikiChunkStore：存储服务（含 Redis 缓存）
│   │   └── pipeline.py             # WikiKnowledgePipeline：流水线入口
│   ├── retrieval/
│   │   ├── init.py
│   │   ├── query_parser.py         # QueryParser：查询解析
│   │   ├── multi_matcher.py        # MultiMatchRetriever：多路匹配
│   │   ├── action_filter.py        # ActionFilter：动作粗筛
│   │   ├── answer_synthesizer.py   # AnswerSynthesizer：答案生成
│   │   └── wiki_retriever.py       # WikiKnowledgeRetriever：检索入口
│   └── review/
│       ├── init.py
│       └── alias_review.py         # AliasReviewService：别名审核服务
└── api/v1/endpoint/
    ├── wiki_knowledge.py          # 【新增】API 端点（入库+检索）
    └── wiki_knowledge_review.py   # 【新增】API 端点（审核）

5.2 扩展点设计（不修改现有代码）

AIBackend/ai-platform-service/app/
├── service/wiki_knowledge/     # 【新增】独立模块
│   ├── models/                 # 数据模型
│   ├── processor/              # 文档处理流水线
│   └── retrieval/              # 检索与答案生成
└── api/v1/endpoint/
    └── wiki_knowledge.py       # 【新增】API 路由（挂载到现有 api_router）

核心原则：
- 所有新代码放在 service/wiki_knowledge/ 目录
- API 端点独立，不修改现有 api/v1/endpoint/ 以外的文件
- 如需修改 api/v1/api.py 引入新路由，仅添加 import 和 include_router 语句

---

六、API 接口设计

6.1 接口列表

接口
方法
路径
功能
文档入库
POST
/api/v1/wiki-knowledge/process
将 Markdown 文档处理入库
知识检索
POST
/api/v1/retrieve/unified
根据问题检索知识并生成答案


/api/v1/wiki-knowledge/retrieve
并发调用两个检索服务，合并结果
待审核列表
GET
/api/v1/wiki-knowledge-review/pending
获取待审核别名列表
确认别名
POST
/api/v1/wiki-knowledge-review/approve
确认别名
拒绝别名
POST
/api/v1/wiki-knowledge-review/reject
拒绝别名

6.2 路由注册

文件：api/v1/api.py（扩展点，不修改已有代码）

from app.api.v1.endpoint import wiki_knowledge

api_router.include_router(
    wiki_knowledge.router,
    prefix="/wiki-knowledge",
    tags=["wiki-knowledge"]
)

6.3 审核页面元素映射（data-testid）

元素
testid
说明
待审核列表容器
wiki-review-pending-list
列表外层容器
列表项
wiki-review-pending-item-{id}
单个待审核项
确认按钮
wiki-review-approve-{id}
确认按钮
拒绝按钮
wiki-review-reject-{id}
拒绝按钮
分页器
wiki-review-pagination
分页组件
知识库筛选下拉
wiki-review-knowledge-filter
按知识库筛选


---

七、复用现有组件

| 组件 | 路径 | 复用方式 |
|------|------|----------|
| SQLUnitOfWork | common/db/database.py | 直接使用 ✅ |
| Response 模型 | common/model/response.py | 直接使用 ✅ |
| BaseEntity | common/model/BaseEntity.py | 继承使用 ✅ |
| get_embedding | rag-pipeline-service/app/service/pooling_client/embedding_client.py | 调用此函数获取向量 |
| unified_agent_invoke | ai-platform-service/app/services/llm_chat/unified_agent.py | 直接使用 ✅ |
| UnifiedAgentRequest | ai-platform-service/app/services/llm_chat/request.py | 直接使用 ✅ |
| API 路由注册模式 | api/v1/api.py | 按现有模式扩展 ✅ |
| 权限控制 | KnowledgeServer | 对接 has_access_to_knowledge 方法 |
Header 工具
common/utils/header_info.py
使用 get_header_value 获取 user-id/role/org-id


---

八、实施计划

> 每个阶段产出可测试的代码模块，阶段完成后进行单元测试验证。

## 阶段一：数据模型

**目标**：定义 WikiChunk、GlobalKG、AliasIndex、ChunkMap 模型

**文件**：
- `models/__init__.py`
- `models/wiki_chunk.py`
- `models/global_kg.py`
- `models/alias_index.py`
- `models/chunk_map.py`

**单元测试**：
- `tests/test_models.py` - 测试模型字段定义、验证规则

**验收标准**：
- [ ] WikiChunk 模型字段正确（chunk_id, doc_id, title_path, content, summary, parent_title, sibling_titles）
- [ ] GlobalKG 模型字段正确（kg_id, standard_name, description, category）
- [ ] AliasIndex 模型字段正确（alias_name, kg_id, pending_review）
- [ ] ChunkMap 模型字段正确（chunk_id, kg_id, weight）
- [ ] 所有模型继承 BaseEntity

---

## 阶段二：存储服务

**目标**：实现 WikiChunkStore，封装 CRUD 操作

**文件**：
- `processor/chunk_store.py`

**单元测试**：
- `tests/test_chunk_store.py` - 使用 SQLite 内存数据库测试 CRUD

**验收标准**：
- [ ] save_chunk() 正确写入 wiki_chunks 表
- [ ] save_kg() 正确写入 global_kg 表
- [ ] save_alias() 正确写入 alias_index 表
- [ ] save_chunk_map() 正确写入 chunk_map 表
- [ ] get_alias_candidates() 正确查询候选实体
- [ ] Redis 缓存更新逻辑正确

---

## 阶段三：切片处理

**目标**：实现 WikiChunkProcessor，将 Markdown 解析为结构化切片

**文件**：
- `processor/chunk_processor.py`

**单元测试**：
- `tests/test_chunk_processor.py` - 使用示例 Markdown 测试切片逻辑

**验收标准**：
- [ ] 按 H1-H4 标题正确切分
- [ ] 每个切片包含 chunk_id, doc_id, title_path, content
- [ ] parent_title 和 sibling_titles 正确提取
- [ ] 空文档或无效输入返回空列表

---

## 阶段四：特征提取（Mock LLM）

**目标**：实现 ContextAwareExtractor.extract()，用 Mock LLM 验证流程

**文件**：
- `processor/context_extractor.py`

**单元测试**：
- `tests/test_context_extractor.py` - Mock unified_agent_invoke，返回预设 JSON

**验收标准**：
- [ ] extract() 正确解析 JSON 响应为 ExtractionResult
- [ ] 构建的 prompt 包含 content、parent_title、sibling_titles
- [ ] JSON 解析异常时返回空 ExtractionResult

**注意**：此阶段使用 Mock LLM，不调用真实接口

---

## 阶段五：实体对齐（Mock LLM）

**目标**：实现 EntityResolver.resolve()，用 Mock LLM 验证裁决流程

**文件**：
- `processor/entity_resolver.py`

**单元测试**：
- `tests/test_entity_resolver.py` - Mock unified_agent_invoke，返回预设置信度

**验收标准**：
- [ ] resolve() 正确处理 NEW、ALIAS、SOFT_LINK 三种裁决类型
- [ ] 置信度 >= 0.85 返回 ALIAS
- [ ] 0.6 <= 置信度 < 0.85 返回 SOFT_LINK
- [ ] 置信度 < 0.6 返回 NEW
- [ ] 无候选实体时直接创建 NEW

---

## 阶段六：流水线整合

**目标**：实现 WikiKnowledgePipeline，串联各组件

**文件**：
- `processor/pipeline.py`

**单元测试**：
- `tests/test_pipeline.py` - Mock 各组件，验证数据流正确 (9 passed, 2026-04-27)

**验收标准**：
- [ ] 文档入库后正确返回统计信息（chunks, entities, alias, new_kg）
- [ ] 切片处理 → 特征提取 → 实体对齐 → 存储 数据流正确
- [ ] 同义词扩展正确处理

---

## 阶段七：查询解析

**目标**：实现 QueryParser，解析用户查询

**文件**：
- `retrieval/query_parser.py`

**单元测试**：
- `tests/test_query_parser.py` - 使用 Mock LLM 测试解析逻辑 (10 passed, 2026-04-27)

**验收标准**：
- [ ] 正确提取 target（目标实体）
- [ ] 正确提取 action（动作词）
- [ ] 解析结果包含 target, action, original_query

---

## 阶段八：多路匹配

**目标**：实现 MultiMatchRetriever，路径匹配 + 实体导航

**文件**：
- `retrieval/multi_matcher.py`

**单元测试**：
- `tests/test_multi_matcher.py` - 使用预设数据测试匹配逻辑 (13 passed, 2026-04-27)

**验收标准**：
- [ ] _path_match() 正确匹配 title_path
- [ ] _entity_navigate() 正确通过 alias_index 导航
- [ ] 合并结果去重

---

## 阶段九：动作过滤与答案生成

**目标**：实现 ActionFilter 和 AnswerSynthesizer

**文件**：
- `retrieval/action_filter.py`
- `retrieval/answer_synthesizer.py`

**单元测试**：
- `tests/test_action_filter.py` - 测试关键词加权排序
- `tests/test_answer_synthesizer.py` - Mock LLM 测试生成逻辑

**验收标准**：
- [ ] ActionFilter 正确过滤不相关切片
- [ ] ActionFilter 按权重排序
- [ ] AnswerSynthesizer 正确生成答案并标注溯源

---

## 阶段十：检索入口与 API

**目标**：实现 WikiKnowledgeRetriever 和 API 端点

**文件**：
- `retrieval/wiki_retriever.py`
- `api/v1/endpoint/wiki_knowledge.py`

**单元测试**：
- `tests/test_wiki_retriever.py` - Mock 各组件测试检索流程
- `tests/test_api.py` - 使用 TestClient 测试 API

**验收标准**：
- [ ] WikiKnowledgeRetriever.retrieve() 返回 AnswerResult
- [ ] API 接口返回正确格式
- [ ] 流式响应正常工作

---

## 阶段十一：集成测试

**目标**：端到端验证完整流程

**验收标准**：
- [ ] 文档入库 → 检索 → 答案生成 全流程正确
- [ ] 与现有 RAG 对比，验证 Wiki 知识库优势
- [ ] 性能基准测试通过


---

九、风险与对策

风险
级别
对策
LLM 裁决质量不足
高
先用人工审核模式，积累足够数据后优化阈值
频繁入库导致数据冗余
中
增加去重机制（基于 content hash）
检索效果不稳定
中
多次采样取平均值，避免偶发异常影响判断
Redis 缓存一致性
低
提供快速验证的小规模测试用例


---

十、核心调用关系

10.1 文档入库

API: wiki_knowledge.process_document()
    ↓
WikiKnowledgePipeline.process_document()
    ↓
    ├─ WikiChunkProcessor.process() → list[ChunkResult]
    ├─ ContextAwareExtractor.extract() → ExtractionResult
    ├─ EntityResolver.resolve() → ResolutionResult
    └─ WikiChunkStore.save_*() → DB

10.2 知识检索

API: wiki_knowledge.retrieve_knowledge()
    ↓
WikiKnowledgeRetriever.retrieve()
    ↓
    ├─ QueryParser.parse() → ParsedQuery
    ├─ MultiMatchRetriever.retrieve() → list[RetrievalCandidate]
    ├─ ActionFilter.filter_and_rank() → list[ScoredChunk]
    └─ AnswerSynthesizer.synthesize() → AnswerResult

