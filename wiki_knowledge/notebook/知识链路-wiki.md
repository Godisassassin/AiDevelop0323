# Wiki 知识库：结构化标签与语义泛化方案 
---

## 目录

- [一、核心设计思想](#一核心设计思想)
- [二、文档入库流水线](#二文档入库流水线)
- [三、存储架构](#三存储架构)
- [四、检索与答案生成](#四检索与答案生成)

---

## 一、核心设计思想

"逻辑关联，物理隔离"

利用 LLM 在预处理阶段的深度理解，将文档转化为带有关联标签的结构化切片。

检索时通过"实体中心"导航，而非模糊的向量相似度计算。

---

## 二、文档入库流水线

### 2.1 目录感知的初级拆分规则

A. 解析规则
- 解析 Markdown/PDF 原始目录结构（H1-H4）

B. 摘要生成
- 直接将该切片的原始标题路径（如：系统配置 > 数据库 > 读写分离）作为该条目的初级摘要

### 2.2 上下文感知的特征提炼 (Context-Aware Extraction)

将当前切片内容、父级标题、同级标题列表同时输入 LLM，提取：

| 类型 | 说明 | 示例 |
|------|------|------|
| 实体 (Entities) | 具象名词 | API 名称、组件名、错误码、特定参数 |
| 概念 (Concepts) | 抽象名词 | 业务逻辑、设计思想、协议原理 |
| 同义词扩展 (Synonym Expansion) | 为每个实体/概念生成 3-5 个潜在搜索关键词 | "用户" 扩展出"客户、访问者" |

### 2.3 实体对齐与冲突处理 (Entity Resolution)

当提取出新实体 Entity_A 时，不直接存储，而是经过以下流程：

```
Entity_A → 候选筛选 → LLM 裁决 → 存储/关联
```

处理方式：

| 裁决结果 | 处理逻辑 |
|----------|----------|
| 等价 (Alias) | 将 Entity_A 存入该实体的同义词库，两个切片共享同一个全局 ID |
| 独立 (New) | 为 Entity_A 创建新的全局实体条目 |
| 关联 (Related) | 仅在两个实体间建立"相关"链接，不合并 |

具体流程：
1. 候选筛选：在全局实体表检索名称相似或已有同义词覆盖的 Top 10 候选实体
2. LLM 裁决：将候选实体定义(当前提取的条目切片)传给 LLM 判断
Prompt 示例：

“请对比实体 A：‘商户’（定义：平台入驻卖家）与实体 B：‘卖家’（定义：在商城开店的用户）。
请从 0-1.0 给出它们的等价置信度。
评估准则： > 1. 如果是全等关系（如 Client 和 客户端），给 0.9 以上；
    2. 如果是包含关系（如 支付 和 微信支付），给 0.6-0.7 并标注 Relation；
    3. 如果只是语义相关但对象不同，给 0.3 以下。”
    S >= 0.85(自动对齐)： 系统判定为同一实体，自动合并同义词库并关联切片。
    S >= 0.6 且 s < 0.85 (人工干预/标记)： 系统建立“软关联”。在前端展示时提示“相关条目”，但在后台不合并。标记为“待审核”。
    S < 0.6 (独立存在)： 判定为新实体，创建独立的 kg_id。

---

## 三、存储架构

### 3.1 存储架构与表结构细节

A. 全局知识图谱表 (Global_KG) —— 知识的大脑
存储唯一的知识节点。

kg_id (UUID/Int): 主键。

standard_name (String): 标准名称（如“水杯”）。

description (Text): 该实体的标准定义，供 LLM 参考。

category (String): 实体或概念的分类（如“硬件”、“业务流程”）。

B. 同义词索引表 (Alias_Index) —— 检索的路标
用于将用户的口语转化为 kg_id。

alias_name (String): 唯一索引。包括标准名和所有同义词（如“商户”、“卖家”）。

kg_id (FK): 指向 Global_KG。

C. 知识切片表 (Wiki_Chunks) —— 知识的肉体
存储最小粒度的文档原文。

chunk_id (UUID): 主键。

title_path (Text): 原始层级标题（如 产品手册 > 维护 > 清理）。对该字段建立全文索引。

content (Text): 实际的段落原文。

doc_id (String): 归属的原始文档 ID，方便溯源。

D. 切片映射表 (Chunk_Map) —— 连接大脑与肉体
kg_id, chunk_id: 复合主键。
存储选型分布表：
暂时无法在飞书文档外展示此内容
### 3.2 具体的存储逻辑与物理文件
切片入库： 文档被 LLM 拆分后的每一段（Chunk）直接存入 Wiki_Chunks 表的 content 字段。

源文件保留： 原始的 PDF 或 Markdown 文件完整地上传到云存储（如阿里云 OSS、S3 或本地 MinIO）。
根据平台已有架构：源文件存在阿里云oss，图片存储在MinIO，源文件路径记录在mysql


用途： 当用户需要“查看完整文档”时，直接给用户跳转链接，而不是从数据库里拼凑。

缓存层：

将 Alias_Index 表的内容全量缓存在 Redis 中。因为同义词映射表数据量相对较小且查询频率极高，缓存后可以将检索预处理的延迟降至最低。

### 3.3 表关系说明

```
Global_KG (核心知识节点)
    ↓ 1:N
Alias_Index (同义词索引)
    ↓ N:1
Chunk_Map (切片映射表)
    ↓ N:1
Wiki_Chunks (知识切片表)
```

---

## 四、检索与答案生成

### 4.1 检索流程

#### Step 1：查询解析

LLM 接收用户问题，提取核心实体与动作。

用户问题解析专家提示词 (Query Parser Prompt)：使用平台的系统提示词功能
Context (背景)
你是一个专门为结构化 Wiki 知识库设计的自然语言理解专家。该知识库不使用向量检索，而是通过“实体导航”和“动作过滤”来定位信息。你的任务是分析用户的原始提问，并将其转化为结构化的检索参数。

Objective (目标)
从用户的提问中提取以下三个核心要素：

Target: 用户询问的知识主体（实体或抽象概念）。

Action: 用户想要对该主体执行的操作或询问的意图。

Action_Synonyms: 基于 Action 扩展出的 3-5 个动词近义词，用于代码层面的关键词匹配。

Style (风格)
你的输出必须是极其精简的 JSON 格式，不包含任何解释性文字或开场白。

Tone (语气)
专业、严谨、逻辑化。

Audience (受众)
后端开发系统的 API 接口，用于驱动后续的 SQL 查询和逻辑过滤。

Response (响应约束)

JSON 结构: 必须包含 target, action, action_synonyms 三个字段。

处理原则:

如果用户问题中包含多个实体，提取最核心的一个。

如果用户意图不明显（如“什么是水杯”），Action 设定为“定义”或“原理”。

Action_Synonyms 必须包含动作本身及其在文档中可能出现的变体。

示例展示 (Few-Shot)
User Input: "如何修改我的个人账户密码？"
Output:

JSON
{
  "target": "账户密码",
  "action": "修改",
  "action_synonyms": ["重置", "设置", "变更", "更名", "更新"]
}
User Input: "如果不小心打碎了玻璃杯该怎么打扫？"
Output:

JSON
{
  "target": "玻璃杯",
  "action": "打扫",
  "action_synonyms": ["清理", "处理", "清扫", "维护", "破损"]
}
User Input: "分布式数据库的读写分离逻辑是什么？"
Output:

JSON
{
  "target": "读写分离",
  "action": "原理",
  "action_synonyms": ["逻辑", "机制", "定义", "概念", "实现方式"]
}


#### Step 2：多路精准匹配

| 匹配方式 | 说明 |
|----------|------|
| 路径匹配 | 检索标题路径中包含核心词的切片 |
| 实体导航 | 根据"客户"在 Alias_Index 中找到对应的 kg_id，拉取关联的所有 Wiki_Chunks |

检索工具链架构 (Tool-Based Retrieval)：联合平台的工作流和工作单元使用
在执行 Step 2 时，系统会并发调用两个核心工具：实体导航工具与路径匹配工具。
工具 A：实体导航器 (Entity_Navigator_Tool)
- 输入： target_entity_name (来自 LLM 解析结果)
- 逻辑：
  1. 首先访问 Alias_Index 表，查询该名称对应的标准 kg_id。
  -- 第一步：精准匹配同义词表SELECT kg_id FROM Alias_Index WHERE alias_name = 'target_entity_name';
  2. 如果未直接命中，调用内部的模糊匹配逻辑查找相似度高的近义词。
  如果精准匹配失败，可以使用 LIKE 'target_entity_name%' 进行前缀匹配作为降级方案。
  3. 返回唯一确定的 kg_id。
- 输出： kg_id (如 UID_CUP)
工具 B：路径扫描器 (Path_Scanner_Tool)
- 输入： target_keywords (实体及相关关键词)
- 逻辑：
  1. 对 Wiki_Chunks 表中的 title_path 字段执行全文检索（Full-text Search）。
  -- 使用 MySQL 的全文索引或联合
   LIKESELECT chunk_id FROM Wiki_Chunks  WHERE title_path LIKE CONCAT('%', 'keyword_1', '%')     OR title_path LIKE CONCAT('%', 'keyword_2', '%');
  2. 利用索引定位标题路径中包含该关键词的所有切片。
- 输出： List[chunk_id]
#### Step 3：实体锚定 (Primary Retrieval)
定位： 核心知识获取工具。它负责将已经对齐的 kg_id 转换为原始的物理知识。
- 输入参数： * kg_id: 经过 Step 1/2 确定的唯一知识节点 ID。
  - min_weight: 可选，过滤掉关联度过低的切片（参考 Chunk_Map 中的 weight 字段）。
- 工具内部逻辑：
  1. 关系检索 (MySQL): 查询 Chunk_Map 表：SELECT chunk_id FROM Chunk_Map WHERE kg_id = ? AND weight >= ?。
  2. 多路匹配的集成逻辑
  将两路返回的 chunk_id 放入一个 Set 集合中。
  优先级打分：如果一个切片同时出现在两路结果中，赋予最高权重。
  系统接收到工具返回的结果后，按照以下优先级进行合并：
暂时无法在飞书文档外展示此内容
  3. 内容拉取 (MongoDB): 利用上一步拿到的 chunk_id 列表，前往 MongoDB 执行 find({_id: {$in: chunk_ids}})。
- 输出结果： * List[RawChunk]: 包含 title_path、content 和 metadata 的对象数组。
#### Step 4：动作粗筛 (Action Filtering)
定位： 知识精炼与降噪工具。它负责在“实体”搬出来的所有卡片中，筛选出符合“动作”意图的那几张。
- 输入参数： * raw_chunks: 实体锚定器返回的原始切片列表。
  - action_intent: 包含 action 和 action_synonyms 的对象。
- 工具内部逻辑：
  1. 关键词向量化模拟（基于关键词加权排序）:
    - 标题匹配 (Score_A): 遍历切片的 title_path。若包含动作词或同义词，得分 $S_A = 10 \times \text{count}$。
    - 内容匹配 (Score_B): 遍历 content。若包含动作词，得分 $S_B = 2 \times \text{count}$。
  2. 动态优先级重排:
    - 计算总分 Score = S_A + S_B。
    - 根据得分进行降序排列。
  3. 截断机制 (Truncation):
    - 仅保留得分最高的前 $N$ 个（通常 $N=3$）。
    - 降级逻辑: 若所有切片得分均为 0（即未发现动作匹配），则按切片的时间戳或重要度默认返回前 2 个，以防完全没有背景。
- 输出结果： * List[RefinedChunk]: 排序后的前 3 个最相关切片。

#### Step 5：精炼生成 (Final Synthesis) —— LLM 负责
将 Top 3 切片投喂给 LLM。

Prompt 模板：
```
基于以下检索到的 {N} 个参考条目，请回答：{Question}。
如果条目间对"客户"和"用户"有不同描述，请分别列出。
```

溯源要求：必须在答案末尾标注引用的原始标题路径。

---

