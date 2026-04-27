Wiki 知识库功能 v2 - 代码实现级计划书

需求来源：notebook/知识链路-wiki.md
遵循规范：ai-obr-dev 技能（/ai-obr-dev）
核心约束：不改变原有代码，通过扩展点新增功能
产出路径：plans/wiki-knowledge-v2-plan.md

---

# 一、现状分析

## 1.1 当前架构

当前无 Wiki 知识库功能，依赖传统 RAG：
- 传统 RAG 采用向量相似度检索
- 切片组织为独立片段，无关联标签
- 知识组织为扁平结构
- 答案生成直接返回切片

## 1.2 当前问题

| 问题 | 描述 |
|------|------|
| 检索精度不足 | 向量相似度无法精准定位实体和概念 |
| 上下文丢失 | 切片独立无关联，无法理解文档层级结构 |
| 同义词处理弱 | 用户口语化表达难以匹配标准术语 |
| 答案质量低 | 直接返回切片，缺乏整合生成能力 |

## 1.3 关键数据流

| 组件 | 存储 | 集合/表 |
|------|------|---------|
| 文档原始内容 | 阿里云 OSS | 源文件存储 |
| 知识切片 | MySQL | wiki_chunks |
| 全局知识图谱 | MySQL | global_kg |
| 别名索引 | MySQL + Redis | alias_index + 缓存 |
| 切片映射 | MySQL | chunk_map |

---

# 二、目标

将传统 RAG 升级为 Wiki 知识库，实现"逻辑关联，物理隔离"：

性能监控数据 → Agent 自动分析 → Agent 自动优化技能/提示词 → 验证效果

## 2.1 具体目标

1. 文档入库流水线：将 Markdown 文档转化为带关联标签的结构化切片
2. 实体对齐与冲突处理：新实体经过候选筛选 → LLM 裁决 → 存储/关联
3. 多路精准检索：路径匹配 + 实体导航，而非向量相似度
4. 动作粗筛：通过动作词匹配过滤并排序切片
5. 答案生成：LLM 基于 Top 3 切片生成答案并标注溯源

## 2.2 与现有 RAG 的区别

| 维度 | 传统 RAG | Wiki 知识库 |
|------|----------|-------------|
| 检索方式 | 向量相似度 | 实体中心导航 + 关键词匹配 |
| 切片组织 | 独立片段 | 带关联标签的结构化切片 |
| 知识组织 | 扁平 | 网状（Entity-Concept 关系） |
| 答案生成 | 直接返回切片 | LLM 整合切片生成答案 |

---

# 三、方案设计

## 3.1 核心思路

新增独立模块 `service/wiki_knowledge/`，包含：
- 文档处理流水线（切片 → 特征提取 → 实体对齐 → 存储）
- 检索与答案生成（查询解析 → 多路匹配 → 动作过滤 → 答案生成）
- 审核服务（别名审核）

## 3.2 架构图

### 3.2.1 文档入库流水线架构

```
文档上传
    ↓
WikiChunkProcessor（切片处理）
    ↓
ContextAwareExtractor（特征提取）
    ↓
EntityResolver（实体对齐）
    ↓
WikiChunkStore（存储）
```

### 3.2.2 检索与答案生成架构

```
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
```

### 3.2.3 存储架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Wiki 知识库存储架构                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │   MySQL     │    │ Meilisearch │    │   Redis     │      │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤      │
│  │ global_kg   │    │ wiki_chunks │    │ Alias_Index │      │
│  │ alias_index │    │ 全文检索    │    │   缓存      │      │
│  │ chunk_map   │    │             │    │             │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                    ┌───────▼───────┐                        │
│                    │  阿里云 OSS   │                        │
│                    │  源文件存储    │                        │
│                    └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**存储分工说明**：
- **Meilisearch**：wiki_chunks（知识切片），提供高速全文检索
- **MySQL**：global_kg（全局知识图谱）、alias_index（同义词索引）、chunk_map（切片映射）
- **Redis**：别名索引缓存、热点数据缓存
- **阿里云 OSS**：源文件存储

## 3.3 数据库设计

### 3.3.1 Wiki_Chunks（知识切片表）

文件：service/wiki_knowledge/models/wiki_chunk.py

```python
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
```

### 3.3.2 Global_KG（全局知识图谱表）

文件：service/wiki_knowledge/models/global_kg.py

```python
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
```

### 3.3.3 Alias_Index（同义词索引表）

文件：service/wiki_knowledge/models/alias_index.py

```python
class AliasIndex(BaseEntity):
    """同义词索引模型，对应 alias_index 表。

    用于将用户的口语转化为 kg_id，是检索的路标。
    继承 BaseEntity：id (BigInteger), create_at, create_by, update_at, update_by, delete_flag
    """
    __tablename__ = "alias_index"

    alias_name = Column("alias_name", String(100), nullable=False, unique=True, index=True)
    kg_id = Column("kg_id", String(36), nullable=False, index=True)
    pending_review = Column("pending_review", Boolean, default=False)
```

### 3.3.4 Chunk_Map（切片映射表）

文件：service/wiki_knowledge/models/chunk_map.py

```python
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
```

### 3.3.5 表关系说明

```
global_kg (核心知识节点)
    ↓ 1:N
alias_index (同义词索引)  [alias_name -> kg_id]
    ↓ N:1
chunk_map (切片映射)  [kg_id, chunk_id]
    ↓ N:1
wiki_chunks (知识切片)  [chunk_id]
```

---

# 四、修改点清单

## 4.1 新增文件

### 4.1.1 数据库模型（4个文件）

| 文件路径 | 说明 |
|----------|------|
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/__init__.py | 模型模块导出 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/wiki_chunk.py | WikiChunk 模型 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/global_kg.py | GlobalKG 模型 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/alias_index.py | AliasIndex 模型 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/models/chunk_map.py | ChunkMap 模型 |

### 4.1.2 文档处理流水线（5个文件）

| 文件路径 | 说明 |
|----------|------|
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/__init__.py | 处理器模块导出 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/chunk_processor.py | WikiChunkProcessor：切片处理 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/context_extractor.py | ContextAwareExtractor：特征提取 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/entity_resolver.py | EntityResolver：实体对齐 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/chunk_store.py | WikiChunkStore：存储服务 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/processor/pipeline.py | WikiKnowledgePipeline：流水线入口 |

### 4.1.3 检索与答案生成（5个文件）

| 文件路径 | 说明 |
|----------|------|
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/__init__.py | 检索模块导出 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/query_parser.py | QueryParser：查询解析 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/multi_matcher.py | MultiMatchRetriever：多路匹配 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/action_filter.py | ActionFilter：动作粗筛 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/answer_synthesizer.py | AnswerSynthesizer：答案生成 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/retrieval/wiki_retriever.py | WikiKnowledgeRetriever：检索入口 |

### 4.1.4 审核服务（1个文件）

| 文件路径 | 说明 |
|----------|------|
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/review/__init__.py | 审核模块导出 |
| AIBackend/rag-pipeline-service/app/service/wiki_knowledge/review/alias_review.py | AliasReviewService：别名审核服务 |

### 4.1.5 API 端点（2个文件）

| 文件路径 | 说明 |
|----------|------|
| AIBackend/rag-pipeline-service/app/api/v1/endpoint/wiki_knowledge.py | 文档入库 + 知识检索 API |
| AIBackend/rag-pipeline-service/app/api/v1/endpoint/wiki_knowledge_review.py | 别名审核 API |

## 4.2 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| AIBackend/rag-pipeline-service/app/api/v1/api.py | 添加 wiki_knowledge 和 wiki_knowledge_review 路由注册 |
| AIBackend/rag-pipeline-service/app/service/knowledge/knowledge.py | 新增 get_knowledge_permission、get_available_knowledge_list 方法调用 |

## 4.3 需新增的方法

| 类/模块 | 方法 | 说明 |
|---------|------|------|
| KnowledgeServer | get_knowledge_permission(org_id, knowledge_id, role, user_id) | 确认是否存在，用于权限校验 |
| KnowledgeServer | get_available_knowledge_list(user_id, role, org_id) | 确认是否存在，获取用户可访问知识库列表 |
| MultiMatchRetriever | _path_match(target, knowledge_ids) | 路径匹配（当前是 pass） |
| MultiMatchRetriever | _entity_navigate(target, knowledge_ids) | 实体导航（当前是 pass） |
| EntityResolver | _candidate_filter(entity_name) | 候选筛选（当前是 pass） |

## 4.4 数据库迁移

```sql
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
```

---

# 五、目录结构

## 5.1 新增文件清单

```
AIBackend/rag-pipeline-service/app/
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
```

## 5.2 扩展点设计（不修改现有代码）

```
AIBackend/rag-pipeline-service/app/
├── service/wiki_knowledge/     # 【新增】独立模块
│   ├── models/                 # 数据模型
│   ├── processor/              # 文档处理流水线
│   └── retrieval/              # 检索与答案生成
└── api/v1/endpoint/
    └── wiki_knowledge.py       # 【新增】API 路由（挂载到现有 api_router）
```

**核心原则**：
- 所有新代码放在 `service/wiki_knowledge/` 目录
- API 端点独立，不修改现有 `api/v1/endpoint/` 以外的文件
- 如需修改 `api/v1/api.py` 引入新路由，仅添加 import 和 include_router 语句

---

# 六、API 接口设计

## 6.1 接口列表

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 文档入库 | POST | /api/v1/wiki-knowledge/process | 将 Markdown 文档处理入库 |
| 知识检索 | POST | /api/v1/wiki-knowledge/retrieve | 根据问题检索知识并生成答案 |
| 待审核列表 | GET | /api/v1/wiki-knowledge-review/pending | 获取待审核别名列表 |
| 确认别名 | POST | /api/v1/wiki-knowledge-review/approve | 确认别名 |
| 拒绝别名 | POST | /api/v1/wiki-knowledge-review/reject | 拒绝别名 |

## 6.2 路由注册

文件：api/v1/api.py（扩展点，不修改已有代码）

```python
from app.api.v1.endpoint import wiki_knowledge

api_router.include_router(
    wiki_knowledge.router,
    prefix="/wiki-knowledge",
    tags=["wiki-knowledge"]
)
```

## 6.3 审核页面元素映射（data-testid）

| 元素 | testid | 说明 |
|------|--------|------|
| 待审核列表容器 | wiki-review-pending-list | 列表外层容器 |
| 列表项 | wiki-review-pending-item-{id} | 单个待审核项 |
| 确认按钮 | wiki-review-approve-{id} | 确认按钮 |
| 拒绝按钮 | wiki-review-reject-{id} | 拒绝按钮 |
| 分页器 | wiki-review-pagination | 分页组件 |
| 知识库筛选下拉 | wiki-review-knowledge-filter | 按知识库筛选 |

---

# 七、复用现有组件

| 组件 | 路径 | 复用方式 |
|------|------|----------|
| SQLUnitOfWork | common/db/database.py | 直接使用 ✅ |
| Response 模型 | common/model/response.py | 直接使用 ✅ |
| BaseEntity | common/model/BaseEntity.py | 继承使用 ✅ |
| get_embedding | rag-pipeline-service/app/service/pooling_client/embedding_client.py | 调用此函数获取向量 |
| LLM 调用 | 通过 embedding-service 外部服务 | 使用 httpx 调用 |
| API 路由注册模式 | api/v1/api.py | 按现有模式扩展 ✅ |
| 权限控制 | KnowledgeServer | 对接 has_access_to_knowledge 方法 |
| Header 工具 | common/utils/header_info.py | 使用 get_header_value 获取 user-id/role/org-id |

---

# 八、实施计划

## 阶段一：数据模型 + 存储

| 任务 | 文件 | 说明 |
|------|------|------|
| 创建 MySQL 表 | models/wiki_chunk.py 等 | WikiChunk、GlobalKG、AliasIndex、ChunkMap |
| 实现存储服务 | processor/chunk_store.py | 使用 SQLUnitOfWork 写入 |
| 单元测试 | tests/test_chunk_store.py | 测试 CRUD 操作 |

## 阶段二：文档入库流水线

| 任务 | 文件 | 说明 |
|------|------|------|
| 切片处理 | processor/chunk_processor.py | 按 H1-H4 解析 Markdown |
| 特征提取 | processor/context_extractor.py | LLM 提取实体/概念/同义词 |
| 实体对齐 | processor/entity_resolver.py | 候选筛选 + LLM 裁决 |
| 流水线整合 | processor/pipeline.py | 串联各组件 |
| 集成测试 | tests/test_pipeline.py | 端到端测试 |

## 阶段三：检索与答案生成

| 任务 | 文件 | 说明 |
|------|------|------|
| 查询解析 | retrieval/query_parser.py | LLM 解析 target/action |
| 多路匹配 | retrieval/multi_matcher.py | 路径匹配 + 实体导航 |
| 动作粗筛 | retrieval/action_filter.py | 关键词加权排序 |
| 答案生成 | retrieval/answer_synthesizer.py | LLM 生成答案 |
| 检索入口 | retrieval/wiki_retriever.py | 串联各组件 |
| API 接口 | api/v1/endpoint/wiki_knowledge.py | 暴露 RESTful 接口 |
| API 测试 | tests/test_api.py | 接口测试 |

## 阶段四：集成测试

| 任务 | 说明 |
|------|------|
| 端到端流程测试 | 文档入库 → 检索 → 答案生成 |
| 性能基准测试 | 延迟、吞吐量 |
| 与现有 RAG 对比 | 验证 Wiki 知识库优势 |

---

# 九、风险与对策

| 风险 | 级别 | 对策 |
|------|------|------|
| LLM 裁决质量不足 | 高 | 先用人工审核模式，积累足够数据后优化阈值 |
| 频繁入库导致数据冗余 | 中 | 增加去重机制（基于 content hash） |
| 检索效果不稳定 | 中 | 多次采样取平均值，避免偶发异常影响判断 |
| Redis 缓存一致性 | 低 | 提供快速验证的小规模测试用例 |

---

# 十、核心调用关系

## 10.1 文档入库

```
API: wiki_knowledge.process_document()
    ↓
WikiKnowledgePipeline.process_document()
    ↓
    ├─ WikiChunkProcessor.process() → list[ChunkResult]
    ├─ ContextAwareExtractor.extract() → ExtractionResult
    ├─ EntityResolver.resolve() → ResolutionResult
    └─ WikiChunkStore.save_*() → DB
```

## 10.2 知识检索

```
API: wiki_knowledge.retrieve_knowledge()
    ↓
WikiKnowledgeRetriever.retrieve()
    ↓
    ├─ QueryParser.parse() → ParsedQuery
    ├─ MultiMatchRetriever.retrieve() → list[RetrievalCandidate]
    ├─ ActionFilter.filter_and_rank() → list[ScoredChunk]
    └─ AnswerSynthesizer.synthesize() → AnswerResult
```
