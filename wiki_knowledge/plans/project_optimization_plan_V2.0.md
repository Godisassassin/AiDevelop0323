# 项目优化计划 V2.0 - 阶段实现方案

## 源文档

本文档为完整版本，整合了原项目优化计划的全部内容，并进行阶段裁剪形成V2.0版本。

---

## 背景

基于原计划书的架构，**阶段一仅实现 1（任务Skill化）+ 2（能力描述化）**。

详见本文档末尾的「与原文档的差异对照」章节。

---

## 一、需求概述

### 1.1 现有系统架构

```
文档上传流程:
前端 (KnowledgeFileUpload.vue)
  -> OSS存储
  -> 调用 /api/v1/document/add
  -> 写入MySQL (Document表)

文档处理流程 (状态机驱动):
状态0: 待处理
  -> 200: 文档转PDF
  -> 300: 图片转PDF
  -> 400: 视频抽音频
  -> 500: 音频转文本
  -> 1000: PDF转Markdown
  -> 1100: 文本切分 (text_split_handler) -> MongoDB
  -> 1200: 向量化 (text_embedding_handler) -> Milvus
  -> 1240: Meilisearch同步
  -> 5000: 成功

文档检索流程:
用户查询
  -> Embedding服务生成向量
  -> Milvus向量搜索
  -> MongoDB获取文本
  -> Rerank重排序
  -> 返回结果
```

### 1.2 现有切分策略的问题

- **字符计数切分**：现有切分按字符数（默认1000字）盲目切分，破坏文档逻辑结构
- **无层级信息**：切分块丢失了原始文档的目录层级信息
- **检索精度不足**：向量检索对专有名词（如"MongoDB"、"OCR"）召回率低
- **上下文断裂**：细碎切分导致LLM无法看到完整章节上下文

### 1.3 优化目标

根据 `知识链路.txt` 实现的三大核心能力：

1. **层级结构化切分**：利用Markdown标题层级实现"章-节-小节"的树状结构切分
2. **智能路由检索**：通过LLM充当"图书管理员"，基于目录结构进行逻辑定位检索
3. **语义元数据注入**：为每个切分块注入Summary和Key_Keywords，提升检索权重

## 二、本版本实现范围

| 架构层级 | 原计划内容 | 本版本实现 | 说明 |
|---------|-----------|-----------|------|
| 1. 任务Skill化 | 封装为标准Skills | ✅ **新增** | 新增执行型Skills：层级切分Skill、语义注入Skill |
| 2. 能力描述化 | Skill Registry能力注册表 | ✅ **新增** | 新建描述表，描述能力而非实现 |

---

## 三、核心新增内容

### 3.1 任务Skill化

**目标**：将"层级切分"、"语义注入"封装为可被Agent调用的执行型Skills。

### 3.1.1 Skill调用模式（重要澄清）

根据实际需求，Skills有三种调用模式：

| Skill | 调用方 | 触发方式 |
|-------|-------|---------|
| HierarchicalChunkSkill | **前端API** | 用户点击上传文档按钮 |
| SemanticInjectSkill | **切分Skill** | 切分完成后自动链式调用 |
| IntelligentRetrieveSkill | **前端API** | 用户进行文档检索时 |

**不是Agent Tool，是服务级Skill**：Skill通过API暴露，客户端直接调用，不经过Agent对话。

### 3.1.2 执行型Skill vs 查询型Skill

| 类型 | 调用方式 | 本版本新增 |
|------|---------|-----------|
| 查询型Skill | Agent调用tool查Skill定义（skills.py已有） | - |
| **执行型Skill** | **前端API直接调用** | ✅ 新增服务级Skill |

### 3.1.3 Skill调用链路

```python
# 切分链路（用户上传文档）
前端 → POST /api/v1/skill/hierarchical_chunk → HierarchicalChunkSkill.execute()
                                                    ↓ 链式调用
                                              SemanticInjectSkill.execute()
                                                    ↓
                                              存储 MongoDB

# 检索链路（用户检索文档）
前端 → POST /api/v1/skill/intelligent_retrieve → IntelligentRetrieveSkill.execute()
                                                    ↓
                                              返回检索结果
```

### 3.2 能力描述化 - Skill Registry

#### 3.2.1 目标

建立**能力注册表**，描述：
- Skill能做什么（而非"调用哪个函数"）
- Skill有哪些参数（带默认值）
- 参数的作用是什么

#### 3.2.2 Skill Registry 数据结构

```json
{
  "skill_id": "hierarchical_chunk",
  "skill_name": "层级结构化切分",
  "capability_description": "将文档按标题层级（章-节-小节）进行结构化切分，保持语义完整性",
  "parameters": [
    {
      "name": "max_chunk_size",
      "type": "int",
      "default": 1000,
      "description": "单块最大字数阈值"
    },
    {
      "name": "min_chunk_size",
      "type": "int",
      "default": 300,
      "description": "单块最小字数阈值"
    }
  ],
  "implementation": "HierarchicalChunkSkill",  // 指向执行类
  "dependencies": ["HierarchicalSplitter"],       // 依赖的切分器
  "capability_type": "document_processing"       // 能力分类
}
```

#### 3.2.3 能力分类

| capability_type | 说明 | 示例Skills |
|-----------------|------|-----------|
| `document_processing` | 文档处理 | 层级切分、知识点重写 |
| `retrieval` | 检索能力 | 向量检索、目录检索、意图分析 |
| `routing` | 路由能力 | **（待后续实现）** | |

#### 3.2.4 能力描述 vs 实现细节

**原计划的"能力描述化"问题**：
- 原计划描述：`"文本片段语义结构化"` 而非 `"调用GPT-4o切分"`
- 本版本实现：Registry中只记录`capability_description`，不记录具体LLM调用

**关键区别**：
```python
# 原计划（概念）
description = "文本片段语义结构化"  # 描述能力

# 实际实现
description = "使用LLM进行智能切分"  # 仍然描述实现
```

本版本采用**折中方案**：描述中包含"何时使用LLM"，但通过`llm_config`参数化，让调用者决定。

---

## 四、详细设计

### 4.1 新增模块清单

| 模块 | 路径 | 功能 | 优先级 |
|------|------|------|--------|
| **Skill Registry** | `AIBackend/rag-pipeline-service/app/skill_registry/` | 能力注册表管理 | P0 |
| **执行型Skills** | `AIBackend/rag-pipeline-service/app/skills/` | 实际执行切分/注入的Skill类 | P0 |
| **Skill加载器** | `AIBackend/rag-pipeline-service/app/skill_registry/loader.py` | 将Skills挂载到Agent | P1 |

### 4.2 Skill Registry 设计

#### 4.2.1 数据模型

**文件**: `AIBackend/rag-pipeline-service/app/skill_registry/models.py`

```python
class SkillRegistryEntry(BaseModel):
    """能力注册表条目"""
    skill_id: str                    # 唯一标识
    skill_name: str                  # 显示名称
    capability_description: str       # 能力描述（做什么）
    parameters: list[SkillParameter]  # 参数列表
    implementation: str               # 实现类路径
    dependencies: list[str]          # 依赖
    capability_type: str             # 能力分类

class SkillParameter(BaseModel):
    """Skill参数定义"""
    name: str
    type: str                        # int, str, bool, list
    default: Any
    description: str
    required: bool = False
```

#### 4.2.2 Registry存储

| 存储 | 说明 |
|------|------|
| MySQL `skill_registry` 表 | 注册表元数据 |
| MongoDB `skill_content` 集合 | 能力描述详细内容 |

### 4.3 执行型Skill设计

#### 4.3.1 设计说明

**服务级Skill，非Agent Tool**：Skill通过FastAPI暴露为REST接口，前端客户端直接调用，不经过Agent对话。

#### 4.3.2 HierarchicalChunkSkill

**文件**: `AIBackend/rag-pipeline-service/app/skills/hierarchical_chunk_skill.py`

```python
class HierarchicalChunkSkill:
    """层级结构化切分Skill - 服务级接口"""

    async def execute(
        self,
        text: str,
        doc_title: str,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 300,
        knowledge_id: str = None,
        document_id: str = None,
    ) -> SkillExecutionResult:
        """
        执行层级结构化切分

        处理流程：
        1. 按标题层级切分文档（章-节-小节）
        2. 标题为数字标号时，调用LLM生成描述性标题
        3. 链式调用SemanticInjectSkill进行语义注入

        Args:
            text: Markdown文档内容
            doc_title: 文档标题
            max_chunk_size: 单块最大字数（超长块不切分，改为LLM重写）
            min_chunk_size: 单块最小字数
            knowledge_id: 知识库ID（用于存储）
            document_id: 文档ID（用于存储）

        Returns:
            SkillExecutionResult: 包含切分结果和状态
        """
        splitter = HierarchicalSplitter()
        chunks = splitter.split_hierarchical(text, doc_title)

        # 处理数字标号标题：调用LLM生成描述性标题
        for chunk in chunks:
            if self._is_numeric_only_title(chunk.title):
                chunk.title = await self._llm_generate_title(
                    chunk.content,
                    chunk.level,
                    doc_title
                )

        # 链式调用语义注入
        semantic_skill = SemanticInjectSkill()
        injected_chunks = await semantic_skill.execute(chunks)

        # 存储到MongoDB
        await self._store_chunks(injected_chunks, knowledge_id, document_id)

        return SkillExecutionResult(
            status="success",
            skill_id="hierarchical_chunk",
            output={"chunk_count": len(injected_chunks)}
        )

    def _is_numeric_only_title(self, title: str) -> bool:
        """
        判断标题是否为纯数字标号

        Args:
            title: 标题文本

        Returns:
            bool: True表示是纯数字标号（如"1.1"、"3.2.1"）
        """
        import re
        # 匹配纯数字标号：1.1, 3.2.1, (1), 【1】等
        pattern = r'^[\d\.\(\)\[\]【】]+$|^\d+$'
        return bool(re.match(pattern, title.strip()))

    async def _llm_generate_title(
        self,
        content: str,
        level: int,
        doc_title: str
    ) -> str:
        """
        调用LLM生成描述性标题

        Args:
            content: 章节内容
            level: 标题层级（1=章, 2=节, 3=小节）
            doc_title: 文档标题

        Returns:
            str: LLM生成的描述性标题
        """
        prompt = f"""
根据以下{level}级章节内容，生成一个简洁的描述性标题（不超过20字）。

文档：{doc_title}
层级：{'章' if level == 1 else '节' if level == 2 else '小节'}
内容预览：{content[:500]}...

请只返回标题，不要其他内容。
"""
        response = await llm_client.chat(prompt)
        return response.strip()

    async def _store_chunks(self, chunks, knowledge_id, document_id):
        """
        存储切分结果到MongoDB

        Args:
            chunks: 注入语义后的块列表
            knowledge_id: 知识库ID
            document_id: 文档ID
        """
        # 实现存储逻辑...
        pass
```

#### 4.3.3 SemanticInjectSkill

**文件**: `AIBackend/rag-pipeline-service/app/skills/semantic_inject_skill.py`

**设计说明**：
- **TextChunk（普通块≤1000字）**：生成summary和keywords，保留原文
- **KnowledgePoint（超长块>1000字）**：LLM重写为若干条知识点，每条包含摘要和关键词，保留原文索引

```python
class SemanticInjectSkill:
    """语义注入Skill - 被HierarchicalChunkSkill链式调用"""

    async def execute(
        self,
        chunks: list[HierarchicalChunk],
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini",
    ) -> list[TextChunk | KnowledgePoint]:
        """
        执行语义注入

        处理逻辑：
        - 普通块（≤1000字）：TextChunk → 生成summary和keywords
        - 超长块（>1000字）：LLM重写为多个KnowledgePoint

        Args:
            chunks: 切分块列表
            llm_provider: LLM供应商
            llm_model: LLM模型

        Returns:
            list[TextChunk | KnowledgePoint]: 注入语义后的块列表
        """
        results = []
        for chunk in chunks:
            if len(chunk.content) <= 1000:
                # 普通块：生成摘要和关键词
                result = await self._inject_text_chunk(chunk)
            else:
                # 超长块：LLM重写为知识点
                results.extend(await self._rewrite_to_knowledge_points(chunk))
            results.append(result)

        return results

    async def _inject_text_chunk(self, chunk: HierarchicalChunk) -> TextChunk:
        """
        为普通块生成摘要和关键词

        Args:
            chunk: 原始块

        Returns:
            TextChunk: 包含summary和keywords
        """
        prompt = f"""
为以下文本生成摘要（≤100字）和3-5个关键词。

文本：
{chunk.content}

返回JSON格式：
{{"summary": "...", "keywords": ["kw1", "kw2", "kw3"]}}
"""
        llm_response = await llm_client.chat(prompt)
        parsed = json.loads(llm_response)

        return TextChunk(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            title=chunk.title,
            title_path=chunk.title_path,
            summary=parsed["summary"],
            keywords=parsed["keywords"],
            breadcrumb=chunk.breadcrumb,
            level=chunk.level,
            source_reference=SourceReference(
                chunk_id=chunk.chunk_id,
                char_start=0,
                char_end=len(chunk.content)
            )
        )

    async def _rewrite_to_knowledge_points(
        self,
        chunk: HierarchicalChunk
    ) -> list[KnowledgePoint]:
        """
        将超长块LLM重写为若干条知识点

        知识点用于检索匹配，命中后通过source_reference返回原文

        Args:
            chunk: 超长块（>1000字）

        Returns:
            list[KnowledgePoint]: 知识点列表
        """
        prompt = f"""
将以下文本重写为3-7条知识点，每条知识点：
1. 独立描述一个子主题
2. 包含摘要（≤50字）和关键词（2-3个）
3. 保留原文位置索引

文本：
{chunk.content}

返回JSON格式：
{{
  "knowledge_points": [
    {{
      "knowledge_content": "知识点内容...",
      "summary": "摘要",
      "keywords": ["kw1", "kw2"],
      "source_char_start": 0,
      "source_char_end": 150
    }}
  ]
}}
"""
        llm_response = await llm_client.chat(prompt)
        parsed = json.loads(llm_response)

        points = []
        for i,kp in enumerate(parsed["knowledge_points"]):
            points.append(KnowledgePoint(
                point_id=f"{chunk.chunk_id}_kp_{i}",
                knowledge_content=kp["knowledge_content"],
                summary=kp["summary"],
                keywords=kp["keywords"],
                source_reference=SourceReference(
                    chunk_id=chunk.chunk_id,
                    char_start=kp["source_char_start"],
                    char_end=kp["source_char_end"]
                )
            ))
        return points


class TextChunk:
    """
    普通文本块（≤1000字）

    用于检索匹配，命中后直接返回content
    """
    chunk_id: str                    # 块唯一标识
    content: str                     # 原文内容
    title: str                       # 标题（数字标号经LLM生成）
    title_path: TitlePath            # 标题路径结构
    summary: str                     # 摘要（LLM生成）
    keywords: list[str]              # 关键词（LLM提取）
    breadcrumb: list[str]            # 面包屑
    level: int                       # 层级
    source_reference: SourceReference # 原文索引


class KnowledgePoint:
    """
    知识点（超长块LLM重写后产生）

    用于检索匹配，命中后通过source_reference返回原文
    """
    point_id: str                    # 知识点ID
    knowledge_content: str           # LLM重写的知识点（用于检索）
    summary: str                     # 知识点摘要
    keywords: list[str]              # 知识点关键词
    source_reference: SourceReference # 原文索引（用于返回原文）


class SourceReference:
    """
    原文索引（检索命中后用于还原原文）

    通过char_start和char_end定位原文位置
    """
    chunk_id: str                   # 所属chunk ID
    char_start: int                 # 原文起始位置
    char_end: int                   # 原文结束位置


class InjectedChunk:
    """注入语义元数据后的chunk（已废弃，统一使用TextChunk和KnowledgePoint）"""
    pass
```

#### 4.3.4 IntelligentRetrieveSkill（智能检索入口）

**文件**: `AIBackend/rag-pipeline-service/app/skills/intelligent_retrieve_skill.py`

**说明**：IntelligentRetrieveSkill 是智能检索的API入口，实际检索逻辑委托给 `IntentAnalysisSkill` + 目录寻址闭环。

```python
class IntelligentRetrieveSkill:
    """智能检索Skill - 用户文档检索时调用"""

    async def execute(
        self,
        query: str,
        knowledge_ids: list[str],
        user_id: str = None,
        role: str = None,
        org_id: str = None,
        retrieval_mode: str = "intelligent",
    ) -> list[RetrievedChunk]:
        """
        执行智能检索

        检索流程：
        1. IntentAnalysisSkill解析用户意图
        2. 目录寻址闭环：定位Node_ID → 提取Content → 还原原文
        3. 通过source_reference返回原文（非知识点重写内容）

        Args:
            query: 检索query
            knowledge_ids: 知识库ID列表
            user_id: 用户ID
            role: 用户角色
            org_id: 机构ID
            retrieval_mode: 检索模式
                - intelligent: 智能路由检索（IntentAnalysisSkill + 目录寻址）
                - vector: 向量检索
                - hybrid: 混合检索
                - fulltext: 全文检索

        Returns:
            list[RetrievedChunk]: 检索结果列表
        """
        if retrieval_mode == "intelligent":
            intent_skill = IntentAnalysisSkill()
            intent_result = await intent_skill.execute(query)
            node_ids = await locate_node_id(intent_result, knowledge_ids)
            return await extract_content(node_ids)
        elif retrieval_mode == "vector":
            return await self._vector_retrieve(query, knowledge_ids, top_k)
        elif retrieval_mode == "hybrid":
            return await self._hybrid_retrieve(query, knowledge_ids, top_k)
        elif retrieval_mode == "fulltext":
            return await self._fulltext_retrieve(query, knowledge_ids, top_k)
        else:
            raise ValueError(f"Unknown retrieval mode: {retrieval_mode}")
```

#### 4.3.5 Skill注册与发现（API层）

**文件**: `AIBackend/rag-pipeline-service/app/api/v1/endpoints/skill_execution.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/skill", tags=["skill"])

@router.post("/hierarchical_chunk")
async def execute_hierarchical_chunk(request: HierarchicalChunkRequest):
    """执行层级切分Skill"""
    skill = HierarchicalChunkSkill()
    result = await skill.execute(
        text=request.text,
        doc_title=request.doc_title,
        max_chunk_size=request.max_chunk_size,
        knowledge_id=request.knowledge_id,
        document_id=request.document_id,
    )
    return result

@router.post("/intelligent_retrieve")
async def execute_intelligent_retrieve(request: IntelligentRetrieveRequest):
    """执行智能检索Skill"""
    skill = IntelligentRetrieveSkill()
    result = await skill.execute(
        query=request.query,
        knowledge_ids=request.knowledge_ids,
        top_k=request.top_k,
        retrieval_mode=request.retrieval_mode,
    )
    return result
```

### 4.4 Agent集成

**本版本不涉及Agent Tool绑定**：Skills通过API调用，不经过Agent。

### 4.5 存储设计

#### 4.5.1 新增MySQL表

```sql
-- 能力注册表
CREATE TABLE skill_registry (
    id BIGINT PRIMARY KEY,
    skill_id VARCHAR(100) UNIQUE NOT NULL,
    skill_name VARCHAR(200) NOT NULL,
    capability_description TEXT,
    implementation VARCHAR(500),
    capability_type VARCHAR(50),
    create_at DATETIME,
    update_by BIGINT,
    delete_flag TINYINT DEFAULT 0
);

-- Skill参数表
CREATE TABLE skill_parameters (
    id BIGINT PRIMARY KEY,
    skill_id VARCHAR(100) NOT NULL,
    param_name VARCHAR(100) NOT NULL,
    param_type VARCHAR(50),
    param_default TEXT,
    param_description TEXT,
    required TINYINT DEFAULT 0
);
```

#### 4.5.2 MongoDB集合（复用）

| 集合 | 用途 |
|------|------|
| `skill_content` | 能力描述详细内容（复用现有） |

---

## 五、API接口设计

### 5.1 Skill Registry API

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 创建Skill | POST | `/api/v1/skill-registry/skill` | 注册新Skill |
| 查询Skill | GET | `/api/v1/skill-registry/skill/{skill_id}` | 获取Skill详情 |
| 更新Skill | PUT | `/api/v1/skill-registry/skill/{skill_id}` | 更新Skill定义 |
| 列表Skill | GET | `/api/v1/skill-registry/skills` | 列表所有Skills |
| 绑定到Agent | POST | `/api/v1/skill-registry/bind` | 绑定Skill到Agent |

### 5.2 Skill执行API

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 执行层级切分 | POST | `/api/v1/skill/hierarchical_chunk` | 执行切分Skill |
| 执行智能检索 | POST | `/api/v1/skill/intelligent_retrieve` | 执行检索Skill |

---

## 六、检索架构

### 6.1 检索流程

```
用户查询
   ↓
1. 意图与关键词提取：IntentAnalysisSkill分析用户问题
   ↓
2. 多级路由定位：
   - 关键词召回：Meilisearch（BM25）锁定文档范围
   - 目录树定位：MongoDB catalog_tree模糊匹配node_id
   - 精准路由：跳过全量向量检索，直接读取目标章节Block
   ↓
3. 上下文还原：通过source_reference返回原文
   ↓
返回检索结果
```

### 6.2 意图解析Skill - IntentAnalysisSkill

**文件**: `AIBackend/rag-pipeline-service/app/skills/intent_analysis_skill.py`

#### 6.2.1 核心工具：System Prompt

```python
INTENT_ANALYSIS_PROMPT = """
# Role: 意图解析 Skill

## Background
用户正在与知识库对话，你需要作为翻译层，将自然语言转化为内部执行参数。

## Goals
1. 识别核心实体（Entity）。
2. 判断操作意图（Intent）。

## Constraints
- 必须严格遵循 JSON 格式。
- 如果无法确定意图，默认赋值为 "GENERAL_QUERY"。

## Workflow
Step 1: 分析用户输入的关键词。
Step 2: 对比预定义的意图列表。
Step 3: 构建输出对象。

## Output Format
```json
{"intent": "...", "params": {...}}
```

## Few-Shot + Chain of Thought (思维链范式)

**实现方式**：在 System Prompt 中加入 2-3 组 `Input -> Thought -> Output` 的示例。

**效果**：能够极大降低模型在面对模糊问题时的"幻觉"和"胡乱分配意图"。
"""
```

#### 6.2.2 IntentAnalysisSkill 实现

```python
class IntentAnalysisSkill:
    """意图解析Skill - 将自然语言转化为内部执行参数"""

    async def execute(
        self,
        query: str,
    ) -> IntentResult:
        """
        分析用户查询，提取意图和参数

        Args:
            query: 用户自然语言查询

        Returns:
            IntentResult: 包含intent和params的解析结果
        """
        # 调用LLM进行意图解析
        result = await self._llm_analyze(query)
        return result

    async def _llm_analyze(self, query: str) -> IntentResult:
        """使用Few-Shot CoT方式调用LLM"""
        # 构建包含Few-Shot示例的prompt
        prompt = self._build_cot_prompt(query)
        response = await llm_client.chat(prompt)
        return self._parse_json_response(response)
```

#### 6.2.3 预定义意图列表

```python
PREDEFINED_INTENTS = {
    "CHAPTER_QUERY": "用户明确要求查看某个章节",
    "ENTITY_QUERY": "用户询问某个实体/概念",
    "TOPIC_QUERY": "用户询问某个主题",
    "COMPARISON_QUERY": "用户要求对比多个内容",
    "SUMMARY_QUERY": "用户要求总结",
    "GENERAL_QUERY": "通用查询"
}

INTENT_PARAMS = {
    "entity": "核心实体（如MongoDB、Redis）",
    "topic": "主题关键词（如分片、索引）",
    "chapter_path": "章节面包屑路径",
    "doc_id": "目标文档ID"
}
```

### 6.3 目录寻址闭环

#### 第一步：定位——从参数到 Node_ID

```python
async def locate_node_id(intent_result: IntentResult, knowledge_ids: list[str]) -> list[str]:
    """
    通过意图解析结果定位Node_ID

    逻辑：
    - 拿着 entity 和 topic 去 MongoDB catalog_tree 查询
    - 模糊匹配标题中包含关键词的节点
    """
    # MongoDB 查询
    query = {
        "knowledge_id": {"$in": knowledge_ids},
        "title": {"$regex": f"{intent_result.params.get('entity', '')}|{intent_result.params.get('topic', '')}", "$options": "i"}
    }
    nodes = await db.catalog_tree.find(query)
    return [node["node_id"] for node in nodes]
```

#### 第二步：提取——从 Node_ID 到 Content

```python
async def extract_content(node_ids: list[str]) -> list[RetrievedChunk]:
    """
    通过Node_ID直接获取内容块

    关联查询：每个Chunk都存储了它所属的node_id
    """
    chunks = await db.document_chunks.find({
        "node_id": {"$in": node_ids}
    }).sort("block_index", 1)

    # 通过source_reference还原原文
    results = []
    for chunk in chunks:
        if chunk.get("knowledge_points"):
            # 超长块：知识点匹配 → 原文还原
            for point in chunk["knowledge_points"]:
                original_text = chunk["content"][point["source_char_start"]:point["source_char_end"]]
                results.append(RetrievedChunk(
                    text=original_text,  # 返回原文
                    source_reference=point["source_reference"]
                ))
        else:
            # 普通块：直接返回
            results.append(RetrievedChunk(text=chunk["content"]))

    return results
```

#### 第三步：还原——上下文增强（向上合并策略）

```python
async def enhance_context(node_id: str) -> str:
    """
    向上溯源，获取父级背景 + 当前节内容
    """
    node = await db.catalog_tree.find_one({"node_id": node_id})
    parent_id = node.get("parent_id")

    if parent_id:
        # 获取父节点摘要或前一个节点的末尾内容
        parent = await db.catalog_tree.find_one({"node_id": parent_id})
        parent_summary = parent.get("summary", "")
        current_content = await extract_content([node_id])
        return f"{parent_summary}\n\n{current_content}"

    return await extract_content([node_id])
```

### 6.4 Agent找数据的三种模式

| 模式 | 路径 | 适用场景 |
|------|------|----------|
| **精确模式 (Exact Path)** | 意图解析 → 面包屑路径 → `db.chunks.find({"breadcrumb": "章>节"})` | 用户明确要求查看某个章节 |
| **语义模式 (Semantic Metadata)** | 意图解析 → 关键词 → `db.chunks.find({"keywords": {"$in": ["分片"]}})` | 目录匹配不明显，但预处理阶段LLM注入了相关关键词 |
| **全量召回模式 (Bulk Load)** | 定位到"章"ID → 拉取下面所有的"节"和"块" | 复杂任务，需要LLM对整章进行总结或对比 |

### 6.5 目录树服务 CatalogTreeService

**文件**: `AIBackend/rag-pipeline-service/app/service/catalog_tree/catalog_tree_service.py`

```python
class CatalogTreeService:
    """
    目录树服务

    功能：
    - 从Markdown文档提取目录结构
    - 存储目录树到MongoDB
    - 提供目录树查询接口
    """

    async def extract_and_save(self, document_id: str, markdown_content: str) -> CatalogTree:
        """提取目录结构并存储"""

    def get_catalog_tree(self, document_id: str) -> CatalogTree:
        """获取文档的目录树"""

    def get_chapter_by_path(self, document_id: str, path: str) -> CatalogNode:
        """根据路径获取章节信息"""
```

---

## 八、开发顺序

**第一阶段**：Skill Registry + 执行型Skills（本文档核心）

1. `SkillRegistryEntry` 模型 + MySQL表
2. `HierarchicalChunkSkill` 执行类
3. `SemanticInjectSkill` 执行类
4. Skill执行API接口
5. Skill Registry管理API

**第二阶段**：目录树服务 + 智能路由检索

- `CatalogTreeService` 类实现
- MongoDB `catalog_tree` 集合
- `IntentAnalysisSkill` 类实现

**第三阶段**：检索优化

- 扩展`TEXT_CHUNK_COLLECTION`字段
- 检索结果合并逻辑

### 8.1 开发顺序详细说明（来自原文档六开发分支规划）

**第一阶段**：结构化切分流水线（含语义注入）
- `HierarchicalSplitter` 类实现（V2.0中复用为Skill实现的后端逻辑）
- 数字标号标题识别与LLM生成描述性标题
- `SemanticInjectService` 类实现（TextChunk/KnowledgePoint两种输出）
- 切分流水线串联集成
- 扩展TEXT_CHUNK_COLLECTION字段（新增knowledge_points等字段）

**第二阶段**：目录树服务
- `CatalogTreeService` 类实现
- MongoDB `catalog_tree` 集合创建与索引

**第三阶段**：智能路由检索
- `IntentAnalysisSkill` 类实现
- 目录寻址闭环实现
- 新增API接口 `intelligent_retrieve.py`
- 检索模式路由分发器

---

## 九、测试验证

### 9.1 单元测试

| 模块 | 测试文件 | 覆盖率要求 |
|------|----------|-----------|
| Skill Registry | `tests/test_skill_registry.py` | ≥80% |
| HierarchicalChunkSkill | `tests/test_hierarchical_chunk_skill.py` | ≥80% |
| SemanticInjectSkill | `tests/test_semantic_inject_skill.py` | ≥80% |
| IntentAnalysisSkill | `tests/test_intent_analysis_skill.py` | ≥80% |

### 9.2 集成测试

1. **Skill注册流程**：创建Skill → 查询Skill → 验证注册结果
2. **切分流程**：上传文档 → 调用HierarchicalChunkSkill → 验证切分结果
3. **语义注入流程**：切分块 → 调用SemanticInjectSkill → 验证摘要生成

---

## 十、与原文档的差异对照

| 原文档章节 | 处理方式 | 说明 |
|-----------|---------|------|
| 4.1 层级切分器 | **修改** | 新增数字标号标题处理（LLM生成描述性标题） |
| 4.2 存储设计 | **修改** | TextChunk和KnowledgePoint两种数据结构分离；超长块LLM重写为知识点 |
| 4.3 智能路由检索 | **重构** | 新增IntentAnalysisSkill，详细实现目录寻址闭环 |
| 6.3 检索模式架构 | **保留** | 智能路由检索 + 向量检索 + 混合检索 |

---

**V2.0版本新增说明**：
- 新增章节：3（核心新增内容）、4.1-4.5（详细设计）、5（API）
- 标题处理：数字标号标题（如"1.1"、"3.2.1"）由LLM生成描述性标题
- 超长块处理：1000字以上不切分，改为LLM重写为知识点（TextChunk/KnowledgePoint分离）
- 检索重构：IntentAnalysisSkill + 目录寻址闭环（定位→提取→还原）